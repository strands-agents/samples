# AWS Health Triage Data

This directory contains clinical data and configuration files used by the AWS Health Triage System - an intelligent medical triage assistant that helps guide patients to the appropriate level of care.

## Overview

The AWS Health Triage System uses a comprehensive decision tree approach to assess patient symptoms and provide personalized care recommendations. The system combines deterministic decision paths with AI-powered reasoning to ensure accurate and safe triage decisions.

## Data Structure

### Primary Decision Tree
- **`comprehensive_decision_tree.json`** - Main decision tree containing all triage pathways
  - 30+ medical specialties covered
  - Emergency, urgent care, and routine care pathways
  - Pediatric, women's health, men's health specializations
  - Mental health crisis intervention
  - Medication and preventive care guidance

### Comprehensive Medical Coverage
1. **Emergency Assessment** - Life-threatening conditions requiring immediate 911 calls
2. **Pain & Injury** - Musculoskeletal, trauma, and pain management
3. **Illness Assessment** - Infectious diseases, fever, general illness
4. **Cardiac Assessment** - Heart conditions and chest pain evaluation
5. **Mental Health** - Crisis intervention, anxiety, depression support
6. **Respiratory** - Breathing difficulties, asthma, COPD management
7. **Pediatric Care** - Age-specific assessments for children
8. **Women's Health** - Pregnancy, gynecological, reproductive health
9. **Men's Health** - Urology, prostate, testosterone concerns
10. **Medication Management** - Drug interactions, side effects, dosing
11. **Preventive Care** - Wellness, screening, health maintenance

### Advanced Features
- **Dynamic Reasoning** - AI-powered decision support for complex cases
- **Safety-First Approach** - Conservative triage with emergency prioritization
- **Session Management** - Conversation state tracking for continuity
- **Multi-Modal Support** - Both structured decisions and free-text chat
- **Edge Case Handling** - Comprehensive coverage of uncommon scenarios

## Node Structure

Each decision tree node contains:
```json
{
  "id": "unique_node_identifier",
  "topic": "User-friendly topic name",
  "question": "Clinical question or assessment",
  "ui_display": "Formatted display with emojis and styling",
  "response_options": ["Option 1", "Option 2", "..."],
  "should_reason": true/false,
  "reasoning_rules": "Clinical reasoning guidelines",
  "additional_reasoning": "Supplementary decision factors",
  "required": true/false,
  "dependencies": ["prerequisite_nodes"],
  "children": ["next_possible_nodes"],
  "is_terminal": true/false,
  "outcome": "care_pathway_recommendation"
}
```

## Outcome Categories

1. **`emergency_care`** - Immediate 911/ER required
2. **`urgent_care`** - Within 24 hours care needed
3. **`routine_care`** - Schedule within days/weeks
4. **`telehealth`** - Virtual consultation appropriate
5. **`self_care`** - Home management with monitoring
6. **`specialist_care`** - Referral to medical specialist
7. **`crisis_intervention`** - Mental health emergency resources

## Usage

The decision tree is loaded by the backend system and serves as the foundation for:
- Interactive patient assessments
- AI-powered reasoning and recommendations  
- Session-based conversation tracking
- Dynamic UI generation
- Clinical pathway routing

## Clinical Safety

This system is designed for guidance only and:
- Always errs on the side of caution
- Prioritizes emergency situations
- Provides clear next steps and resources
- Includes crisis intervention pathways
- Maintains detailed reasoning trails

## Data Updates

To update the decision tree:
1. Modify `comprehensive_decision_tree.json`
2. Restart the backend service to reload data
3. Test all pathways for clinical accuracy
4. Validate emergency routing functionality

---

**Important**: This triage system is for guidance only and does not replace professional medical judgment. Always seek immediate medical attention for emergencies. 