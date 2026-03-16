# DealFlow AI - Product Requirements Document

## Objective
DealFlow AI is an AI-powered assistant that helps relationship managers analyze client conversations, detect financial needs, recommend banking products, check eligibility, and route tasks to the correct internal agents.

## Target Users
1. Bank Clients
2. Relationship Managers
3. Product Specialists
   - Loan Specialist
   - Credit Card Specialist
   - Trade Finance Specialist

## Core Features
1. Conversation analysis
2. Financial product recommendation
3. Policy-aware decision making using retrieval-augmented generation (RAG)
4. Eligibility rule engine
5. Task generation
6. Task routing
7. Client-agent messaging workflow

## Actors
- Client
- Relationship Manager
- Loan Specialist
- Credit Card Specialist
- Trade Finance Specialist

## Core Workflow
Client sends message
-> AI analyzes conversation
-> Product recommendation generated
-> Eligibility evaluated
-> Task generated
-> Assigned to correct actor

## Example Scenario
Client: "We want to expand our truck fleet."

Expected AI output:
- Product: Vehicle Loan
- Eligibility: Eligible
- Assigned Agent: Loan Specialist
- Task: Schedule loan consultation

## Success Criteria
- The system extracts actionable needs from conversation threads.
- The system recommends a banking product with supporting rationale.
- The system evaluates eligibility using explicit business rules.
- The system creates and assigns a follow-up task to the correct internal role.
- Users can review conversation history, AI insights, and generated tasks in the UI.
