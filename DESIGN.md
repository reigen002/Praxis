---
name: Praxis
description: A calm operating desk for evidence-backed founder decisions
colors:
  primary: "#5b55d6"
  primary-hover: "#4842b5"
  canvas: "#f6f7fa"
  surface: "#ffffff"
  ink: "#202b40"
  muted: "#626d80"
  navigation: "#192136"
  border: "#e5e8ef"
  success: "#26715a"
  critical: "#ad3e45"
  attention: "#926313"
typography:
  body:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "DM Sans Variable, DM Sans, sans-serif"
    fontSize: "13px"
    fontWeight: 500
rounded:
  control: "7px"
  surface: "14px"
spacing:
  compact: "8px"
  control: "14px"
  panel: "24px"
  workspace: "36px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
---

# Design System: Praxis

## Overview

**Creative North Star: "The founder's operating desk"**

Operate mode. An ink navy navigation rail frames a cool pale canvas and white
working surfaces. Indigo identifies actions; amber/red communicate urgency.
Evidence and real task state lead the interface. This document records the
implemented React surface, replacing the former Streamlit visual guidance.

Source, interaction and actual Chrome captures support these rules. The final
desktop rehearsal covers 1440×1000 and 1366×768, with an emulated mobile overview
at 390×844. Independent review found no material visible defect in the ten
captured states. This is scoped visual evidence, not full accessibility approval.

## Colors

CSS primitives live in `frontend/src/styles.css`. Ink is for essential content,
muted for secondary text, and borders separate surfaces. Keep status labels
alongside color. Preserve the distinct light text palette on the navy rail.

## Typography

Self-hosted DM Sans Variable provides one consistent UI family; system sans is
the fallback. Main copy is approximately fourteen pixels, metadata eleven to
thirteen, and page titles approximately thirty pixels. Financial figures use
tabular numerals with cents retained. Do not encode key information only in tiny
metadata. These sizes are extracted from source, not a claim of full accessibility.

## Layout

Desktop rail is 238px and the top bar 73px. The content container is capped at
1530px with 36px horizontal spacing. Metrics precede the founder question and
two-column briefing/evidence area. CSS adapts at 1600, 1250, 1000, 760 and 480px.
At 760px the rail becomes a dismissible menu; the closed rail is hidden from
focus. At narrower sizes cards stack and tables retain horizontal scrolling.

## Elevation & Depth

Fine borders and tonal changes define ordinary surfaces. The evidence drawer
uses a translucent backdrop and a soft left shadow to establish modal depth.
Primary actions have a small ambient shadow; no floating decorative panels.

## Shapes

Fourteen-pixel surface corners and seven-pixel controls form the repeated shape
vocabulary. Compact status chips use five-pixel corners. Icons are Lucide SVG;
the three-bar brand mark is authored CSS. No raster artwork is shipped.

## Components

- **Primary buttons:** indigo, white text, clear hover/focus and disabled states.
  Secondary buttons remain white with a fine border. Pending actions lock inputs.
- **Metric strip:** exact deterministic figures with definitions and source cohorts.
- **Priority cards:** rank, textual urgency, impact, next step, owner and source IDs.
- **Evidence drawer:** native dialog, observed record facts and related-record links.
  Escape/close preserves familiar modal behavior.
- **Follow-up cards:** proposed copy plus explicit local approve/reject controls.
- **Decision lab:** baseline and provider result retain different score/probability
  semantics. Genuine cached output keeps its original evaluation timestamp.
- **Navigation:** active state has a lighter navy/indigo surface. Mobile dismissal
  restores toggle focus. Reduced-motion settings disable animation.

## Do's and Don'ts

- Do distinguish source facts, model judgments and recommendations in labels.
- Do preserve exact metric definitions and source ID access.
- Do show errors, pending state and actual saved-result provenance.
- Don't fabricate agent events, charts, provider results or success states.
- Don't replace source evidence with decorative summaries or hide uncertainty.

Remaining limits: captures verify their displayed viewports/states, not every
browser, device or interaction. Small-label and color checks are not a complete
accessibility audit. No such approval is claimed here.
