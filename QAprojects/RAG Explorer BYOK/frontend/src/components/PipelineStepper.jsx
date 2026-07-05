const STAGES = [
  { key: "source", label: "PDF / Upload" },
  { key: "chunk", label: "Chunking" },
  { key: "embed", label: "Embedding" },
  { key: "store", label: "ChromaDB Storage" },
  { key: "retrieve", label: "Retrieval" },
  { key: "llm", label: "LLM Answer" },
];

export default function PipelineStepper({ activeStage, doneStages }) {
  return (
    <div className="stepper">
      {STAGES.map((stage, i) => {
        const isActive = activeStage === stage.key;
        const isDone = doneStages.includes(stage.key);
        return (
          <div key={stage.key} className="stepper-item">
            <div
              className={
                "stepper-dot" +
                (isActive ? " stepper-dot--active" : "") +
                (isDone ? " stepper-dot--done" : "")
              }
            >
              {isDone ? "✓" : i + 1}
            </div>
            <div className={"stepper-label" + (isActive ? " stepper-label--active" : "")}>
              {stage.label}
            </div>
            {i < STAGES.length - 1 && <div className="stepper-line" />}
          </div>
        );
      })}
    </div>
  );
}
