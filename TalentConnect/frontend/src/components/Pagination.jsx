export default function Pagination({ page, pages, onChange }) {
  if (pages <= 1) return null;
  const nums = [];
  for (let i = Math.max(1, page - 2); i <= Math.min(pages, page + 2); i++) nums.push(i);
  return (
    <div className="pagination">
      <button disabled={page <= 1} onClick={() => onChange(page - 1)}>← Précédent</button>
      {nums.map((n) => (
        <button key={n} className={n === page ? "on" : ""} onClick={() => onChange(n)}>{n}</button>
      ))}
      <button disabled={page >= pages} onClick={() => onChange(page + 1)}>Suivant →</button>
    </div>
  );
}
