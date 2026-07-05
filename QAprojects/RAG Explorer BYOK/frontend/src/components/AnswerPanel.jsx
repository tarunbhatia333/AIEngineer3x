export default function AnswerPanel({ answer, error }) {
  if (error) {
    return (
      <div className="answer answer--error">
        <h3>Error</h3>
        <p>{error}</p>
      </div>
    );
  }
  if (!answer) return null;
  return (
    <div className="answer">
      <h3>Answer</h3>
      <p>{answer}</p>
    </div>
  );
}
