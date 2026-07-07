# Distributed Transactions — The Saga Pattern

## The Problem

A traditional database transaction (ACID) guarantees all-or-nothing across a single database. In a microservices architecture, a single business operation (e.g., "place an order") often spans multiple services, each with its own database — Order Service, Inventory Service, Payment Service — and there is no single database transaction that can span all three atomically.

## The Saga Pattern

Breaks a multi-step business operation into a sequence of local transactions, each in its own service, where every step has a corresponding **compensating transaction** to undo it if a later step fails.

```text
1. Order Service: Create Order (local transaction)
2. Inventory Service: Reserve Stock (local transaction)
3. Payment Service: Charge Card (local transaction)

If step 3 fails:
   Compensate step 2: Release Reserved Stock
   Compensate step 1: Cancel Order
```

## Two Coordination Styles

**Choreography** — each service publishes an event when its step completes, and the next service reacts to that event; no central coordinator.

```text
OrderCreated → InventoryReserved → PaymentCharged
   (each service listens for the previous event and acts)
```

Simple for a short saga, but the overall flow becomes implicit and hard to see in one place as more steps are added.

**Orchestration** — a central coordinator (e.g., AWS Step Functions) explicitly calls each service in sequence and handles failure/compensation logic itself.

```text
Step Functions → calls Order Service
              → calls Inventory Service
              → calls Payment Service
              → on failure, calls compensating actions in reverse
```

More visible and easier to reason about as complexity grows, at the cost of introducing a coordinator as a new component.

## AWS Step Functions as an Orchestrator

Step Functions is a natural fit for orchestrated sagas — its state machine model maps directly onto "do step, on failure do compensation," with built-in retry, error handling, and visual execution history, which matters a great deal when debugging why a specific saga instance failed halfway through.

## Senior-Level Considerations

- Compensating transactions are not automatic rollbacks — they're new, explicitly-written business logic ("release stock," "refund payment") and need the same care and testing as the forward path, arguably more, since they run precisely during failure scenarios that are harder to test exhaustively
- Sagas provide eventual consistency, not atomicity — there's a real window where "Order Created" exists but payment hasn't succeeded yet, and the rest of the system needs to handle that intermediate state correctly (e.g., not show the order as confirmed prematurely)
- Choose choreography for short, stable sagas with few steps; choose orchestration once the flow has enough steps or conditional branches that "what happens in what order" is no longer obvious from reading each service's code independently
