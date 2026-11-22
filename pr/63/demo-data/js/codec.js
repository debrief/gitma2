// Spec 035 FR-042/043: a DemoScenario in the URL fragment (deflate-raw JSON, base64url) and as
// a JSON file validated against the LinkML-generated JSON Schema (demo-scenario.schema.json,
// extracted from src/tma2/types/generated/tma.schema.json by scripts/site/demo_schema.py).

const b64url = (bytes) => {
  let s = "";
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
};
const unb64url = (str) => {
  const s = atob(str.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((str.length + 3) % 4));
  return Uint8Array.from(s, (c) => c.charCodeAt(0));
};

async function pipeThrough(bytes, stream) {
  const out = new Response(new Blob([bytes]).stream().pipeThrough(stream));
  return new Uint8Array(await out.arrayBuffer());
}

// "s=" + compressed, or "j=" + plain base64url where CompressionStream is missing
export async function encodeFragment(sc) {
  const bytes = new TextEncoder().encode(JSON.stringify(sc));
  if (typeof CompressionStream !== "undefined") return "s=" + b64url(await pipeThrough(bytes, new CompressionStream("deflate-raw")));
  return "j=" + b64url(bytes);
}

export async function decodeFragment(frag) {
  const f = frag.replace(/^#/, "");
  if (f.startsWith("s=")) {
    const bytes = await pipeThrough(unb64url(f.slice(2)), new DecompressionStream("deflate-raw"));
    return JSON.parse(new TextDecoder().decode(bytes));
  }
  if (f.startsWith("j=")) return JSON.parse(new TextDecoder().decode(unb64url(f.slice(2))));
  return null;
}

// A validator for the JSON Schema subset the LinkML generator emits for these classes:
// $ref into $defs, type (object, array, number, integer, string, boolean, null and lists of
// them), required, properties, additionalProperties: false, items, minItems, maxItems,
// minimum, maximum, enum, anyOf. Returns a list of messages (empty when valid).
export function validate(schema, value, root = schema, path = "$") {
  const errs = [];
  if (schema.$ref) {
    const name = schema.$ref.replace(/^#\/\$defs\//, "");
    return validate(root.$defs[name], value, root, path);
  }
  if (schema.anyOf) {
    const ok = schema.anyOf.some((s) => validate(s, value, root, path).length === 0);
    if (!ok) errs.push(`${path}: matches none of the allowed forms`);
    return errs;
  }
  if (schema.type) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    const is = (t) =>
      t === "null" ? value === null
      : t === "array" ? Array.isArray(value)
      : t === "object" ? value !== null && typeof value === "object" && !Array.isArray(value)
      : t === "integer" ? Number.isInteger(value)
      : t === "number" ? typeof value === "number" && Number.isFinite(value)
      : typeof value === t;
    if (!types.some(is)) {
      errs.push(`${path}: expected ${types.join(" or ")}, got ${value === null ? "null" : Array.isArray(value) ? "array" : typeof value}`);
      return errs;
    }
  }
  if (schema.enum && !schema.enum.includes(value)) errs.push(`${path}: ${JSON.stringify(value)} is not one of ${schema.enum.join(", ")}`);
  if (typeof value === "number") {
    if (schema.minimum !== undefined && value < schema.minimum) errs.push(`${path}: ${value} is below the minimum ${schema.minimum}`);
    if (schema.maximum !== undefined && value > schema.maximum) errs.push(`${path}: ${value} is above the maximum ${schema.maximum}`);
  }
  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) errs.push(`${path}: needs at least ${schema.minItems} items`);
    if (schema.maxItems !== undefined && value.length > schema.maxItems) errs.push(`${path}: allows at most ${schema.maxItems} items`);
    if (schema.items) value.forEach((v, i) => errs.push(...validate(schema.items, v, root, `${path}[${i}]`)));
  } else if (value !== null && typeof value === "object") {
    for (const r of schema.required || []) if (!(r in value) || value[r] === undefined) errs.push(`${path}: missing required "${r}"`);
    const props = schema.properties || {};
    for (const [k, v] of Object.entries(value)) {
      if (props[k]) errs.push(...validate(props[k], v, root, `${path}.${k}`));
      else if (schema.additionalProperties === false) errs.push(`${path}: unknown field "${k}"`);
    }
  }
  return errs;
}

// rules the JSON Schema cannot state
export function checkScenario(schema, sc) {
  const errs = validate(schema, sc);
  if (errs.length) return errs;
  if (!(sc.window.end_s > sc.window.start_s)) errs.push("$.window: end_s must be after start_s");
  return errs;
}
