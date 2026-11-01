module.exports = {
  docs: [
    { type: "doc", id: "index", label: "Welcome" },
    { type: "doc", id: "glossary", label: "Glossary" },
    { type: "doc", id: "data-dictionary", label: "Data dictionary" },
    {
      type: "category",
      label: "Algorithms",
      items: ["algorithms/physics-layer", "algorithms/gate1-model", "algorithms/least-squares", "algorithms/ekf-imm", "algorithms/crb"],
    },
  ],
};
