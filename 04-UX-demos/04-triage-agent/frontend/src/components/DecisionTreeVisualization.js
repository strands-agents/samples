import React, { useEffect, useRef, useState } from 'react';
import Tree from 'react-d3-tree';
import './DecisionTreeVisualization.css';

const DecisionTreeVisualization = ({ tree, currentNodeId }) => {
  const treeContainerRef = useRef(null);
  const [treeData, setTreeData] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const prevNodeIdRef = useRef(null);

  useEffect(() => {
    if (tree && tree.nodes) {
      const convertToD3Format = (nodeId, nodes) => {
        const node = nodes[nodeId];
        if (!node) return null;

        const isCurrentNode = nodeId === currentNodeId;
        const hasChildren = node.children && node.children.length > 0;

        return {
          name: node.topic || (nodeId === 'start' ? 'Start Node' : nodeId),
          attributes: {
            id: nodeId,
            isCurrentNode,
            isTerminal: node.is_terminal,
            hasChildren
          },
          children: hasChildren ? 
            node.children.map(childId => convertToD3Format(childId, nodes)).filter(Boolean) : 
            []
        };
      };

      const d3TreeData = convertToD3Format('start', tree.nodes);
      setTreeData(d3TreeData);
      
      // 노드 ID가 변경되었을 때 중앙 정렬
      if (currentNodeId && prevNodeIdRef.current !== currentNodeId) {
        prevNodeIdRef.current = currentNodeId;
        // GitHub 이슈 해결법: translate 리셋 후 재설정
        setTimeout(() => {
          setDimensions(prev => ({ ...prev, width: prev.width + 1 })); // Force re-render
          setTimeout(() => {
            setDimensions(prev => ({ ...prev, width: prev.width - 1 }));
          }, 50);
        }, 100);
      }
    }
  }, [tree, currentNodeId]);

  useEffect(() => {
    const updateDimensions = () => {
      if (treeContainerRef.current) {
        const { offsetWidth, offsetHeight } = treeContainerRef.current;
        setDimensions({ width: offsetWidth, height: offsetHeight });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const renderCustomNode = ({ nodeDatum, toggleNode }) => {
    const { attributes } = nodeDatum;
    const isCurrentNode = attributes?.isCurrentNode;
    const isTerminal = attributes?.isTerminal;
    const hasChildren = attributes?.hasChildren;

    return (
      <g>
        <circle
          r={15}
          fill={isCurrentNode ? '#3b82f6' : (isTerminal ? '#ef4444' : '#6b7280')}
          stroke={isCurrentNode ? '#1d4ed8' : '#374151'}
          strokeWidth={2}
          onClick={toggleNode}
          style={{ cursor: hasChildren ? 'pointer' : 'default' }}
        />
        <text
          fill={isCurrentNode ? '#ffffff' : '#1f2937'}
          strokeWidth="0"
          x={0}
          y={0}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="10"
        >
          {isCurrentNode ? '📍' : (hasChildren ? '📂' : '📄')}
        </text>
        <text
          fill="#1f2937"
          strokeWidth="0"
          x={0}
          y={25}
          textAnchor="middle"
          fontSize="12"
          fontWeight={isCurrentNode ? 'bold' : 'normal'}
        >
          {nodeDatum.name.length > 20 ? 
            `${nodeDatum.name.substring(0, 20)}...` : 
            nodeDatum.name
          }
        </text>
        {isTerminal && (
          <text
            fill="#ef4444"
            strokeWidth="0"
            x={0}
            y={40}
            textAnchor="middle"
            fontSize="10"
            fontWeight="bold"
          >
            End
          </text>
        )}
      </g>
    );
  };

  if (!tree || !tree.nodes || !tree.nodes.start) {
    return (
      <div className="tree-container empty-tree">
        <p>No decision tree data available.</p>
      </div>
    );
  }

  if (!treeData || dimensions.width === 0) {
    return (
      <div ref={treeContainerRef} className="tree-container loading-tree">
        <p>Loading decision tree...</p>
      </div>
    );
  }

  return (
    <div ref={treeContainerRef} className="tree-container">
      <Tree
        data={treeData}
        orientation="horizontal"
        translate={{ x: dimensions.width / 2 - 100, y: dimensions.height / 2 }}
        zoom={0.7}
        scaleExtent={{ min: 0.4, max: 1.5 }}
        separation={{ siblings: 0.8, nonSiblings: 1.2 }}
        nodeSize={{ x: 180, y: 80 }}
        renderCustomNodeElement={renderCustomNode}
        pathFunc="step"
        transitionDuration={300}
        enableLegacyTransitions={true}
        shouldCollapseNeighborNodes={false}
        collapsible={true}
        initialDepth={3}
        depthFactor={200}
        onNodeClick={(nodeData) => {
          // 노드 클릭 시 해당 노드가 현재 노드인지 확인
          if (nodeData.data.attributes && nodeData.data.attributes.isCurrentNode) {
            // 현재 노드로 스크롤
            const nodeElement = document.querySelector('.current-node');
            if (nodeElement) {
              nodeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          }
        }}
      />
    </div>
  );
};

export default DecisionTreeVisualization; 