export default function Chips({ matched = [], missing = [], plain = [] }) {
  return (
    <div className="chips">
      {matched.map((s) => <span key={`m${s}`} className="chip ok">✓ {s}</span>)}
      {missing.map((s) => <span key={`x${s}`} className="chip miss">{s}</span>)}
      {plain.map((s) => <span key={`p${s}`} className="chip">{s}</span>)}
    </div>
  );
}
