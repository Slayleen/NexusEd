import { useState } from "react";
import { US_STATES, citiesForState, parseLocation } from "@/constants/locations";

/**
 * AreaPicker — pick a home area from the full US dataset. Value is a "City, ST" string.
 */
export function AreaPicker({ value, onChange, testidPrefix = "area" }) {
  const init = parseLocation(value);
  const [state, setState] = useState(init.state);
  const [city, setCity] = useState(init.city);
  const cities = state ? citiesForState(state, [city]) : [];

  const emit = (st, c) => onChange(st && c ? `${c}, ${st}` : "");

  const onState = (e) => {
    const st = e.target.value;
    setState(st);
    setCity("");
    emit(st, "");
  };
  const onCity = (e) => {
    const c = e.target.value;
    setCity(c);
    emit(state, c);
  };

  return (
    <div className="grid grid-cols-2 gap-2 mt-1">
      <select className="nb-input" value={state} onChange={onState} data-testid={`${testidPrefix}-state`}>
        <option value="">State…</option>
        {US_STATES.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
      </select>
      <select className="nb-input" value={city} onChange={onCity} disabled={!state} data-testid={`${testidPrefix}-city`}>
        <option value="">City…</option>
        {cities.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
    </div>
  );
}

/**
 * AreaFilter — filter by area using the full U.S. states + cities dataset.
 * value = { state, city }. state/city of "all" means no constraint at that level.
 */
export function AreaFilter({ state, city, onChange, testidPrefix = "opp" }) {
  const cities = state === "all" ? [] : citiesForState(state);

  return (
    <div className="grid grid-cols-2 gap-2">
      <select className="nb-input py-2" value={state}
        onChange={(e) => onChange({ state: e.target.value, city: "all" })} data-testid={`${testidPrefix}-state-select`}>
        <option value="all">All states</option>
        {US_STATES.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
      </select>
      <select className="nb-input py-2" value={city} disabled={state === "all"}
        onChange={(e) => onChange({ state, city: e.target.value })} data-testid={`${testidPrefix}-city-select`}>
        <option value="all">All cities</option>
        {cities.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
    </div>
  );
}
