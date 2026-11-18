import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { InfraStack } from '../lib/infra-stack';

function synth(context?: Record<string, string>): Template {
  const app = new cdk.App({ context });
  return Template.fromStack(new InfraStack(app, 'TestStack'));
}

function albIngress(template: Template): any[] {
  const [lb] = Object.values(template.findResources('AWS::ElasticLoadBalancingV2::LoadBalancer')) as any[];
  const groupId = lb.Properties.SecurityGroups[0]['Fn::GetAtt'][0];
  return template.findResources('AWS::EC2::SecurityGroup')[groupId].Properties.SecurityGroupIngress;
}

test('load balancer is internal by default and only reachable from the VPC', () => {
  const template = synth();

  template.hasResourceProperties('AWS::ElasticLoadBalancingV2::LoadBalancer', { Scheme: 'internal' });
  const ingress = albIngress(template);
  expect(ingress).toHaveLength(1);
  expect(ingress[0]).toMatchObject({ FromPort: 80, ToPort: 80 });
  expect(ingress[0].CidrIp).toEqual({ 'Fn::GetAtt': [expect.stringMatching(/^VPC/), 'CidrBlock'] });
});

test('allowedCidrs makes the load balancer internet-facing for those ranges only', () => {
  const template = synth({ allowedCidrs: '203.0.113.4/32, 198.51.100.0/24' });

  template.hasResourceProperties('AWS::ElasticLoadBalancingV2::LoadBalancer', { Scheme: 'internet-facing' });
  expect(albIngress(template).map((rule) => rule.CidrIp).sort()).toEqual(['198.51.100.0/24', '203.0.113.4/32']);
});

test('rejects an allowedCidrs value that is not a CIDR', () => {
  expect(() => synth({ allowedCidrs: 'true' })).toThrow();
});
