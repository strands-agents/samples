# Strands Agents Samples Repository

This is a staging repository for Strands Agents SDK samples, synced to the public [strands-agents/samples](https://github.com/strands-agents/samples) repository.

## General Guidelines

- Samples are for **demonstration and educational purposes** - not production-ready
- Follow existing sample structure conventions from `.github/templates/02-samples/`
- Always use "Amazon Bedrock" (not "AWS Bedrock") in documentation and code comments
- Use `kebab-case` for directory names

## TypeScript Samples

TypeScript samples are located in the `typescript/` directory.

### Coding Guidelines

- Use TypeScript strict mode
- Prefer async/await over callbacks
- Include proper type definitions
- Avoid `any` types where possible

### Sample Structure

Each TypeScript sample should include:

- `README.md` - Setup instructions and overview
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `.env.example` - Environment variables template (if needed)
