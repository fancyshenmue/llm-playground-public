# LoRA Development Lifecycle

## Overview

This document describes the complete lifecycle of LoRA model development using llm-utils.

## Development Lifecycle Diagram

```mermaid
graph TD
    Start([Start: New LoRA Concept]) --> Define[Define Concept & Topic]
    Define --> DataGen[Data Generation]
    DataGen --> Tag[Image Tagging]
    Tag --> Train[LoRA Training]
    Train --> Test[Generate Test Images]
    Test --> Evaluate{Quality Acceptable?}

    Evaluate -->|Yes| Finalize[Finalize LoRA]
    Evaluate -->|No| Analyze[Analyze Issues]

    Analyze --> Decision{What's Wrong?}
    Decision -->|Poor Training Data| DataGen
    Decision -->|Wrong Parameters| AdjustParams[Adjust Training Config]
    Decision -->|Need More Data| MoreData[Generate More Images]

    AdjustParams --> Train
    MoreData --> Tag

    Finalize --> Publish[Publish/Deploy LoRA]
    Publish --> End([End: LoRA Ready])

    style Start fill:#32CD32
    style End fill:#32CD32
    style Evaluate fill:#FFA500
    style Decision fill:#FFA500
    style Finalize fill:#4169E1
```

## Data Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Concept: Define topic

    Concept --> Generation: llm-utils data-gen
    Generation --> RawImages: 50+ images + captions

    RawImages --> Tagging: llm-utils tag
    Tagging --> TaggedDataset: Images with WD14 tags

    TaggedDataset --> Training: llm-utils train
    Training --> LoRAModel: .safetensors file

    LoRAModel --> Testing: Generate with LoRA
    Testing --> TestResults: Evaluation images

    TestResults --> QualityCheck: llm-utils rank
    QualityCheck --> Analysis: llm-utils analyze

    Analysis --> Decision

    Decision --> Archive: If successful
    Decision --> Refinement: If needs work

    Refinement --> RawImages: More/better data
    Refinement --> Training: Adjust parameters

    Archive --> [*]
```

## Typical Timeline

```mermaid
gantt
    title LoRA Development Timeline (Single Iteration)
    dateFormat  HH:mm
    axisFormat %H:%M

    section Data Prep
    Generate 50 images      :data1, 00:00, 2h
    Tag images             :data2, after data1, 10m
    Review & filter        :data3, after data2, 20m

    section Training
    Setup config           :train1, after data3, 15m
    Train LoRA (1600 steps):train2, after train1, 3h

    section Testing
    Generate test images   :test1, after train2, 30m
    Rank images           :test2, after test1, 10m
    Analyze best results  :test3, after test2, 20m

    section Decision
    Review & decide       :dec1, after test3, 30m
```

**Total Time: ~7-8 hours per iteration**

## Iteration Patterns

### Pattern 1: Quick Iteration (Testing Parameters)

```mermaid
flowchart LR
    A[Existing Dataset] --> B[Adjust Config]
    B --> C[Train v2]
    C --> D[Test]
    D --> E{Better?}
    E -->|Yes| F[Keep v2]
    E -->|No| B

    style A fill:#A9A9A9
    style F fill:#32CD32
```

**Timeline**: 3-4 hours (skip data generation)

### Pattern 2: Data Refinement

```mermaid
flowchart LR
    A[v1 Results] --> B[Analyze Issues]
    B --> C[Generate Focused Data]
    C --> D[Merge with v1 Data]
    D --> E[Retrain v2]
    E --> F[Test]

    style A fill:#FF69B4
    style F fill:#4169E1
```

**Timeline**: 5-6 hours (targeted data generation)

### Pattern 3: Complete Overhaul

```mermaid
flowchart LR
    A[v1 Failed] --> B[Redefine Concept]
    B --> C[New Dataset]
    C --> D[New Training Config]
    D --> E[Train v2]
    E --> F[Test]

    style A fill:#FF6B6B
    style F fill:#4ECDC4
```

**Timeline**: Full 7-8 hours (start from scratch)

## State Machine: LoRA Quality States

```mermaid
stateDiagram-v2
    [*] --> Untrained

    Untrained --> Training: Start training
    Training --> Undertrained: <500 steps
    Training --> Trained: 500-2000 steps
    Training --> Overtrained: >2000 steps

    Undertrained --> Training: Continue
    Trained --> Testing: Test quality
    Overtrained --> Undertrained: Reduce steps

    Testing --> Poor: Score <6
    Testing --> Good: Score 6-7
    Testing --> Excellent: Score 8-10

    Poor --> Analysis: Diagnose
    Good --> Refinement: Minor tweaks
    Excellent --> Production: Deploy

    Analysis --> Untrained: Retry
    Refinement --> Training: Adjust

    Production --> [*]

    note right of Trained
        Sweet spot:
        1000-1600 steps
    end note

    note right of Excellent
        Publishable
        quality
    end note
```

## Resource State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle: System ready

    Idle --> DataGeneration: llm-utils data-gen
    DataGeneration --> Idle: Complete

    Idle --> Tagging: llm-utils tag
    Tagging --> Idle: Complete

    Idle --> Training: llm-utils train
    Training --> GPUBusy: Training active
    GPUBusy --> Idle: Training complete

    Idle --> Testing: llm-utils data-gen --lora
    Testing --> Idle: Complete

    note right of GPUBusy
        GPU at 100%
        Don't start Forge!
        Memory: 16-20GB
    end note

    note right of Idle
        GPU available
        Can run Forge
        for generation
    end note
```

## Decision Tree: When to Iterate

```mermaid
flowchart TD
    Start{Test Results} --> Score{Average Score?}

    Score -->|8-10| Ship[Ship It! ✅]
    Score -->|6-7| Minor[Minor Issues]
    Score -->|<6| Major[Major Issues]

    Minor --> MinorQ{What's wrong?}
    MinorQ -->|Slight oversaturation| Params1[Adjust CFG scale]
    MinorQ -->|Minor artifacts| Params2[Adjust steps/LR]
    MinorQ -->|Inconsistent style| Data1[Add more varied data]

    Major --> MajorQ{What's wrong?}
    MajorQ -->|Doesn't learn concept| Data2[Completely new dataset]
    MajorQ -->|Generic/no effect| Config1[Increase network dim]
    MajorQ -->|Distorted| Config2[Reduce learning rate]

    Params1 --> Quick[Quick iteration]
    Params2 --> Quick
    Data1 --> Medium[Medium iteration]

    Data2 --> Full[Full iteration]
    Config1 --> Medium
    Config2 --> Quick

    Quick --> Retrain1[Train v2<br/>~3h]
    Medium --> Retrain2[Train v2<br/>~5h]
    Full --> Retrain3[Train v2<br/>~8h]

    Retrain1 --> Start
    Retrain2 --> Start
    Retrain3 --> Start

    Ship --> End([Published LoRA])

    style Ship fill:#32CD32
    style Quick fill:#4169E1
    style Medium fill:#FFA500
    style Full fill:#FF69B4
    style End fill:#228B22
```

## Best Practices

### Data Generation Phase
- **Diversity**: Vary prompts, angles, lighting, time of day
- **Quality over Quantity**: 50 good images > 200 mediocre
- **Consistency**: Ensure concept is clear in all images

### Training Phase
- **Start Conservative**:
  - network_dim: 128
  - learning_rate: 1 (with Prodigy)
  - steps: 1200-1600

- **Monitor Loss**: Should decrease steadily

### Testing Phase
- **Generate Variety**: Test different scenarios
- **Batch Evaluate**: Use `llm-utils rank` on all test images
- **Deep Dive**: Use `llm-utils analyze` on best AND worst

### Iteration Strategy
1. **First Iteration**: Always complete (data + train + test)
2. **Second Iteration**: Usually parameter tweaks (3-4h)
3. **Third+ Iteration**: Only if needed (diminishing returns)

## Common Failure Modes

```mermaid
mindmap
  root((LoRA Failures))
    No Effect
      Network dim too small
      Learning rate too low
      Not enough steps
    Overfitting
      Too many steps
      Learning rate too high
      Insufficient data diversity
    Artifacts
      Corrupt training images
      Wrong base model
      Bad tags/captions
    Inconsistent
      Contradictory training data
      Multiple unrelated concepts
      Poor data quality
```

## Success Metrics

| Metric | Poor | Acceptable | Excellent |
|--------|------|------------|-----------|
| Average Rank Score | <5 | 6-7 | 8-10 |
| Concept Recognition | Weak | Clear | Strong |
| Style Consistency | Varies | Mostly | Always |
| Artifact Presence | Frequent | Rare | None |
| Training Time | >8h iterations | 4-6h iterations | 3-4h iterations |

## Automation Opportunities

```bash
# Full automated workflow (with human checkpoints)
#!/bin/bash

# Phase 1: Data Generation
llm-utils data-gen --topic "$CONCEPT" --total 50 --output ./dataset
echo "Review generated images. Continue? (y/n)"
read response
[[ "$response" != "y" ]] && exit

# Phase 2: Tagging
llm-utils tag --path ./dataset

# Phase 3: Training
llm-utils train --config $CONFIG_PATH
echo "Training complete. Test? (y/n)"
read response
[[ "$response" != "y" ]] && exit

# Phase 4: Testing
llm-utils data-gen --lora "${CONCEPT}_v1.safetensors" --total 10 --output ./test
llm-utils rank --dir ./test

echo "Check results and decide on next iteration"
```

This represents the complete lifecycle from concept to published LoRA! 🎯
