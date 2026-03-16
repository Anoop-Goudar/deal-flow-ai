# DealFlow AI POC Brief

## App URL
- Frontend: `https://deal-flow-ai-frontend.vercel.app/`

Optional:
- Backend API: `https://deal-flow-ai-backend.vercel.app/`

Before sharing this document, replace the placeholder frontend URL with the live Vercel app URL.

## What This POC Is
DealFlow AI is a proof of concept for helping relationship managers turn client conversations into actionable banking recommendations.

The app reads a conversation, identifies likely financial needs, checks those needs against policy rules, and suggests the next action for the bank team.

## What The POC Demonstrates
1. Conversation understanding
   The app reads client messages and tries to detect needs such as:
   - Vehicle Loan
   - Trade Finance
   - Business Credit Card
   - Equipment Loan

2. Policy-aware recommendations
   The app retrieves matching internal policy content before forming the recommendation.

3. Eligibility checks
   The app compares client details such as turnover, years in operation, collateral, and trade activity against product rules.

4. Task routing
   The app creates next-step tasks and routes them to the right role, such as:
   - Relationship Manager
   - Loan Specialist
   - Trade Finance Specialist
   - Credit Card Specialist

5. Suggested replies
   The app proposes agent replies based on the latest conversation and current recommendation state.

## Simple End-To-End Flow
1. A client sends a message
   Example: `We want to expand our truck fleet.`

2. The app detects the likely need
   Example: `Vehicle Loan`

3. The app retrieves policy criteria
   Example: business should be operating for more than 2 years

4. The app checks eligibility
   Example: `Eligible`, `Not eligible`, or `Eligibility incomplete`

5. The app recommends the next action
   Example: `Schedule vehicle loan consultation`

6. The app creates or updates a task
   Example: assigned to the relevant banker or specialist

## Main Screens
### 1. Agent Dashboard
Used by the relationship manager.

It shows:
- Conversation timeline
- AI summary
- Detected needs
- Eligibility result
- Policy match
- Suggested replies
- Task board

### 2. Client Portal
Used to simulate the client side of the conversation.

It allows:
- Sending client messages
- Updating the conversation dynamically

### 3. Admin Page
Used for demo control.

It allows:
- Viewing the conversation JSON
- Manually re-running the pipeline
- Resetting demo state

## Suggested Demo Scenarios
### Scenario A: Eligible Vehicle Loan
Use this client message:
`Our turnover is $8M, we have operated for 5 years, and the vehicles can be used as collateral.`

Expected outcome:
- Vehicle Loan appears
- Eligibility becomes `Eligible`
- Task is routed to the right specialist

### Scenario B: Add Trade Finance Need
Use this client message:
`We also support export routes to Europe and need help with trade-related payments.`

Expected outcome:
- Trade Finance appears in addition to Vehicle Loan

### Scenario C: Make The Case Ineligible
Use this client message:
`Actually, we have only been operating for 1 year.`

Expected outcome:
- Eligibility changes to `Not eligible`
- Suggested replies become explanation-oriented
- Tasks shift toward relationship-manager follow-up instead of specialist consultation

### Scenario D: Ask A Criteria Question
Use this client message:
`What's the criteria?`

Expected outcome:
- Suggested replies should explain the product criteria and the current eligibility gap

## What To Pay Attention To
- How the AI summary changes as the conversation changes
- How client attributes get updated from conversation messages
- How recommendations change when the client shares new facts
- How the suggested replies update with the latest context
- How tasks move from pending to in progress to completed

## Current POC Limitations
This is a proof of concept, not a production system yet.

Current limitations:
- App state is still in-memory, so data may reset across redeploys or cold starts
- No authentication yet
- No persistent database yet
- Suggested replies are rule-guided and context-aware, but not yet full production-quality conversational banking guidance
- This is designed for internal demo and validation, not external customer use

## What Good Looks Like In This POC
The POC is successful if teammates can see that:
- conversations can be translated into banking needs
- product recommendations can be grounded in policy criteria
- eligibility can change dynamically when new facts are provided
- tasks and next actions can be routed automatically
- the experience feels like a useful banker copilot, not just a chatbot

## Feedback To Collect From Teammates
Ask teammates:
- Did the recommendations feel believable?
- Did the eligibility logic make sense?
- Were the next actions useful?
- Did the suggested replies sound natural?
- What product flows should be added next?
- What information should be persisted in a real implementation?
