import { useState } from "react";

export default function SearchBar({ initial = {}, onSearch, big = false }) {
  const [q, setQ] = useState(initial.q || "");
  const [location, setLocation] = useState(initial.location || "");
  const [offerType, setOfferType] = useState(initial.offer_type || "");

  const submit = (e) => {
    e.preventDefault();
    onSearch({ q: q.trim(), location: location.trim(), offer_type: offerType });
  };

  return (
    <form className={`searchbar ${big ? "big" : ""}`} onSubmit={submit}>
      <div className="sfield"><span>🔍</span>
        <input placeholder="Métier, compétence ou entreprise" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <div className="sfield"><span>📍</span>
        <input placeholder="Ville ou région" value={location} onChange={(e) => setLocation(e.target.value)} />
      </div>
      <div className="sfield narrow">
        <select value={offerType} onChange={(e) => setOfferType(e.target.value)}>
          <option value="">Emploi et stage</option>
          <option value="emploi">Emploi</option>
          <option value="stage">Stage</option>
        </select>
      </div>
      <button className="btn" type="submit">Rechercher</button>
    </form>
  );
}
