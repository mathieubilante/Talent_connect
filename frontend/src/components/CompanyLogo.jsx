import { colorFor, initials } from "../utils";

export default function CompanyLogo({ name, size = 52 }) {
  return (
    <div className="clogo" style={{ width: size, height: size, background: colorFor(name), fontSize: size * 0.36 }}>
      {initials(name)}
    </div>
  );
}
