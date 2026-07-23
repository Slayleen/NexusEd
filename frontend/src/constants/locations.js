// US states + major cities used for area selection.
// Locations are stored as "City, ST".

export const US_STATES = [
  { code: "AL", name: "Alabama" }, { code: "AK", name: "Alaska" }, { code: "AZ", name: "Arizona" },
  { code: "AR", name: "Arkansas" }, { code: "CA", name: "California" }, { code: "CO", name: "Colorado" },
  { code: "CT", name: "Connecticut" }, { code: "DE", name: "Delaware" }, { code: "DC", name: "District of Columbia" },
  { code: "FL", name: "Florida" }, { code: "GA", name: "Georgia" }, { code: "HI", name: "Hawaii" },
  { code: "ID", name: "Idaho" }, { code: "IL", name: "Illinois" }, { code: "IN", name: "Indiana" },
  { code: "IA", name: "Iowa" }, { code: "KS", name: "Kansas" }, { code: "KY", name: "Kentucky" },
  { code: "LA", name: "Louisiana" }, { code: "ME", name: "Maine" }, { code: "MD", name: "Maryland" },
  { code: "MA", name: "Massachusetts" }, { code: "MI", name: "Michigan" }, { code: "MN", name: "Minnesota" },
  { code: "MS", name: "Mississippi" }, { code: "MO", name: "Missouri" }, { code: "MT", name: "Montana" },
  { code: "NE", name: "Nebraska" }, { code: "NV", name: "Nevada" }, { code: "NH", name: "New Hampshire" },
  { code: "NJ", name: "New Jersey" }, { code: "NM", name: "New Mexico" }, { code: "NY", name: "New York" },
  { code: "NC", name: "North Carolina" }, { code: "ND", name: "North Dakota" }, { code: "OH", name: "Ohio" },
  { code: "OK", name: "Oklahoma" }, { code: "OR", name: "Oregon" }, { code: "PA", name: "Pennsylvania" },
  { code: "RI", name: "Rhode Island" }, { code: "SC", name: "South Carolina" }, { code: "SD", name: "South Dakota" },
  { code: "TN", name: "Tennessee" }, { code: "TX", name: "Texas" }, { code: "UT", name: "Utah" },
  { code: "VT", name: "Vermont" }, { code: "VA", name: "Virginia" }, { code: "WA", name: "Washington" },
  { code: "WV", name: "West Virginia" }, { code: "WI", name: "Wisconsin" }, { code: "WY", name: "Wyoming" },
];

export const STATE_NAME = Object.fromEntries(US_STATES.map((s) => [s.code, s.name]));

// A practical set of major cities per state (kept concise). Add more as needed.
export const CITIES_BY_STATE = {
  AL: ["Birmingham", "Montgomery", "Huntsville", "Mobile"],
  AK: ["Anchorage", "Fairbanks", "Juneau"],
  AZ: ["Phoenix", "Tucson", "Mesa", "Scottsdale", "Tempe"],
  AR: ["Little Rock", "Fayetteville", "Fort Smith"],
  CA: ["Los Angeles", "San Francisco", "San Diego", "San Jose", "Sacramento", "Oakland", "Palo Alto", "Berkeley", "Irvine"],
  CO: ["Denver", "Colorado Springs", "Boulder", "Aurora"],
  CT: ["Hartford", "New Haven", "Stamford", "Bridgeport"],
  DE: ["Wilmington", "Dover", "Newark"],
  DC: ["Washington"],
  FL: ["Miami", "Orlando", "Tampa", "Jacksonville", "Tallahassee"],
  GA: ["Atlanta", "Savannah", "Athens", "Augusta"],
  HI: ["Honolulu", "Hilo"],
  ID: ["Boise", "Idaho Falls"],
  IL: ["Chicago", "Springfield", "Naperville", "Evanston", "Champaign"],
  IN: ["Indianapolis", "Bloomington", "Fort Wayne"],
  IA: ["Des Moines", "Iowa City", "Cedar Rapids"],
  KS: ["Wichita", "Kansas City", "Lawrence"],
  KY: ["Louisville", "Lexington"],
  LA: ["New Orleans", "Baton Rouge"],
  ME: ["Portland", "Augusta", "Bangor"],
  MD: ["Baltimore", "Annapolis", "Rockville", "Bethesda"],
  MA: ["Boston", "Cambridge", "Worcester", "Springfield", "Somerville", "Lowell"],
  MI: ["Detroit", "Ann Arbor", "Grand Rapids", "Lansing"],
  MN: ["Minneapolis", "Saint Paul", "Rochester"],
  MS: ["Jackson", "Gulfport"],
  MO: ["St. Louis", "Kansas City", "Columbia", "Springfield"],
  MT: ["Billings", "Missoula", "Bozeman"],
  NE: ["Omaha", "Lincoln"],
  NV: ["Las Vegas", "Reno", "Henderson"],
  NH: ["Manchester", "Concord", "Nashua"],
  NJ: ["Newark", "Jersey City", "Princeton", "Trenton"],
  NM: ["Albuquerque", "Santa Fe"],
  NY: ["New York", "Brooklyn", "Buffalo", "Rochester", "Albany", "Ithaca", "Syracuse"],
  NC: ["Charlotte", "Raleigh", "Durham", "Chapel Hill"],
  ND: ["Fargo", "Bismarck"],
  OH: ["Columbus", "Cleveland", "Cincinnati", "Dayton"],
  OK: ["Oklahoma City", "Tulsa", "Norman"],
  OR: ["Portland", "Eugene", "Salem"],
  PA: ["Philadelphia", "Pittsburgh", "Harrisburg", "Allentown"],
  RI: ["Providence", "Newport"],
  SC: ["Charleston", "Columbia", "Greenville"],
  SD: ["Sioux Falls", "Rapid City"],
  TN: ["Nashville", "Memphis", "Knoxville", "Chattanooga"],
  TX: ["Houston", "Austin", "Dallas", "San Antonio", "Fort Worth"],
  UT: ["Salt Lake City", "Provo"],
  VT: ["Burlington", "Montpelier"],
  VA: ["Richmond", "Arlington", "Alexandria", "Norfolk", "Charlottesville"],
  WA: ["Seattle", "Spokane", "Tacoma", "Bellevue"],
  WV: ["Charleston", "Morgantown"],
  WI: ["Milwaukee", "Madison", "Green Bay"],
  WY: ["Cheyenne", "Casper"],
};

// Parse "City, ST" -> { city, state }
export function parseLocation(loc) {
  if (!loc) return { city: "", state: "" };
  const parts = loc.split(",").map((s) => s.trim());
  if (parts.length >= 2) return { city: parts[0], state: parts[1] };
  return { city: parts[0], state: "" };
}

// Return the list of cities for a state code, including any extra city already in use.
export function citiesForState(code, extra = []) {
  const base = CITIES_BY_STATE[code] || [];
  const set = new Set(base);
  extra.forEach((c) => c && set.add(c));
  return Array.from(set).sort();
}
