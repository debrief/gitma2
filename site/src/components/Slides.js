// Embed a reveal.js deck from static/slides/<slug>/index.html in a blog post.
import React from "react";
import useBaseUrl from "@docusaurus/useBaseUrl";

export default function Slides({ slug, title, ratio = 0.5625 }) {
  const src = useBaseUrl(`/slides/${slug}/index.html`);
  return (
    <figure style={{ margin: "1.5rem 0" }}>
      <div style={{ position: "relative", width: "100%", paddingBottom: `${ratio * 100}%` }}>
        <iframe
          src={src}
          title={title || `Slides: ${slug}`}
          loading="lazy"
          allowFullScreen
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            border: "1px solid var(--ifm-color-emphasis-300)",
            borderRadius: "6px",
          }}
        />
      </div>
      <figcaption style={{ fontSize: "0.85rem", marginTop: "0.4rem" }}>
        Use the arrow keys inside the deck, or <a href={src}>open it full screen</a>.
      </figcaption>
    </figure>
  );
}
