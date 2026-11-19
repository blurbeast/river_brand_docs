// Typst preamble for the Riverbrand Knowledge Book PDF builds.
#set page(margin: (x: 2.4cm, y: 2.6cm))
#set text(font: ("Source Serif 4", "New Computer Modern"), size: 10.5pt)
#show raw: set text(font: ("JetBrains Mono", "DejaVu Sans Mono"), size: 9pt)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(1.2em)
  text(size: 20pt, weight: "bold", it)
  v(0.8em)
}
#show heading.where(level: 2): set text(size: 14pt)
#show heading.where(level: 3): set text(size: 12pt)
#show figure: set block(breakable: true)
#set figure.caption(position: top)
#show link: set text(fill: rgb("#0f766e"))
#show quote: set block(inset: (x: 1.2em), stroke: (left: 3pt + rgb("#0f766e")))
