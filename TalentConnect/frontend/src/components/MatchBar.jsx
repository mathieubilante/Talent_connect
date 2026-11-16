export default function MatchBar({ score, level }) {
  if (score === null || score === undefined) return null;
  return (
    <div className="matchbar" title={`Compatibilité : ${level}`}>
      <div className="bar"><div className={`fill ${level}`} style={{ width: `${Math.max(score, 3)}%` }} /></div>
      <span className={`score ${level}`}>{score}%</span>
    </div>
  );
}
