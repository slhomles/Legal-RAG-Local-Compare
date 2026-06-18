// Build slide deck for Legal RAG project (Vietnamese).
// Run: node build_deck.js

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625
pres.author = "Legal RAG Team";
pres.title = "He thong phan tich hop dong phap ly bang RAG";

// ============================================================
// PALETTE (Navy + Gold, legal/professional)
// ============================================================
const NAVY = "0F1E3D";
const MID_NAVY = "2C4A7C";
const GOLD = "C9A961";
const GOLD_DK = "9C7F3F";
const CREAM = "F4F1EA";
const LIGHT = "F4F6FA";
const PANEL = "FFFFFF";
const BORDER = "D6DCE6";
const TEXT_DARK = "1A1A1A";
const TEXT_MUTED = "64748B";
const WHITE = "FFFFFF";
const RED = "B85042";
const GREEN = "2C5F2D";

const HEAD_FONT = "Georgia";
const BODY_FONT = "Calibri";

const W = 10;
const H = 5.625;

// ============================================================
// HELPERS
// ============================================================
function addHeader(slide, kicker, title) {
  // top gold rule
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 0.08, fill: { color: GOLD }, line: { color: GOLD },
  });
  if (kicker) {
    slide.addText(kicker.toUpperCase(), {
      x: 0.5, y: 0.25, w: 6, h: 0.32,
      fontSize: 10, fontFace: BODY_FONT, bold: true,
      color: GOLD_DK, charSpacing: 4, margin: 0,
    });
  }
  slide.addText(title, {
    x: 0.5, y: 0.55, w: 9, h: 0.7,
    fontSize: 28, fontFace: HEAD_FONT, bold: true,
    color: NAVY, margin: 0,
  });
}

function addFooter(slide, pageNo, totalPages) {
  slide.addShape(pres.shapes.LINE, {
    x: 0.5, y: H - 0.4, w: W - 1.0, h: 0,
    line: { color: BORDER, width: 0.5 },
  });
  slide.addText("Legal RAG  ·  Phan tich hop dong phap ly", {
    x: 0.5, y: H - 0.35, w: 6, h: 0.3,
    fontSize: 9, fontFace: BODY_FONT,
    color: TEXT_MUTED, margin: 0,
  });
  slide.addText(`${pageNo} / ${totalPages}`, {
    x: W - 1.5, y: H - 0.35, w: 1.0, h: 0.3,
    fontSize: 9, fontFace: BODY_FONT,
    color: TEXT_MUTED, align: "right", margin: 0,
  });
}

function stepBadge(slide, x, y, num) {
  // gold circle with step number
  slide.addShape(pres.shapes.OVAL, {
    x: x, y: y, w: 0.7, h: 0.7,
    fill: { color: GOLD }, line: { color: GOLD },
  });
  slide.addText(String(num), {
    x: x, y: y, w: 0.7, h: 0.7,
    fontSize: 22, fontFace: HEAD_FONT, bold: true,
    color: WHITE, align: "center", valign: "middle", margin: 0,
  });
}

// rounded info card
function card(slide, x, y, w, h, fill = PANEL, border = BORDER) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fill },
    line: { color: border, width: 0.75 },
    shadow: { type: "outer", color: "000000", blur: 8, offset: 1, angle: 90, opacity: 0.08 },
  });
}

function arrow(slide, x, y, w, color = MID_NAVY) {
  // a horizontal flat arrow: line + triangle
  slide.addShape(pres.shapes.LINE, {
    x, y, w, h: 0,
    line: { color, width: 2 },
  });
  slide.addShape(pres.shapes.RIGHT_TRIANGLE, {
    x: x + w - 0.06, y: y - 0.09, w: 0.18, h: 0.18,
    fill: { color }, line: { color },
    rotate: 90,
  });
}

function pipelineBox(slide, x, y, w, h, title, sub, fill = PANEL) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fill }, line: { color: BORDER, width: 0.75 },
    shadow: { type: "outer", color: "000000", blur: 6, offset: 1, angle: 90, opacity: 0.1 },
  });
  // gold left rule
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.06, h,
    fill: { color: GOLD }, line: { color: GOLD },
  });
  slide.addText(title, {
    x: x + 0.15, y: y + 0.08, w: w - 0.2, h: 0.32,
    fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
  });
  if (sub) {
    slide.addText(sub, {
      x: x + 0.15, y: y + 0.42, w: w - 0.2, h: h - 0.5,
      fontSize: 9.5, fontFace: BODY_FONT, color: TEXT_MUTED, margin: 0,
    });
  }
}

// ============================================================
// SLIDE 1 — TITLE
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  // gold accent block left
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.25, h: H, fill: { color: GOLD }, line: { color: GOLD },
  });
  // subtle stamp circle
  s.addShape(pres.shapes.OVAL, {
    x: W - 2.2, y: 0.5, w: 1.6, h: 1.6,
    fill: { color: NAVY, transparency: 0 },
    line: { color: GOLD, width: 1.5 },
  });
  s.addShape(pres.shapes.OVAL, {
    x: W - 2.0, y: 0.7, w: 1.2, h: 1.2,
    fill: { color: NAVY },
    line: { color: GOLD, width: 0.75 },
  });
  s.addText("LEGAL\nRAG", {
    x: W - 2.0, y: 0.7, w: 1.2, h: 1.2,
    fontSize: 14, fontFace: HEAD_FONT, bold: true,
    color: GOLD, align: "center", valign: "middle", margin: 0,
  });

  s.addText("ĐỒ ÁN", {
    x: 0.7, y: 1.0, w: 6, h: 0.4,
    fontSize: 12, fontFace: BODY_FONT, bold: true,
    color: GOLD, charSpacing: 6, margin: 0,
  });
  s.addText("Hệ thống phân tích\nhợp đồng pháp lý bằng RAG", {
    x: 0.7, y: 1.5, w: 8.5, h: 1.8,
    fontSize: 36, fontFace: HEAD_FONT, bold: true,
    color: WHITE, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 3.25, w: 0.6, h: 0.04,
    fill: { color: GOLD }, line: { color: GOLD },
  });
  s.addText("Phát hiện thay đổi giữa các phiên bản hợp đồng, trích dẫn nguồn và sinh báo cáo — toàn bộ chạy cục bộ.", {
    x: 0.7, y: 3.4, w: 8.5, h: 0.7,
    fontSize: 15, fontFace: BODY_FONT, italic: true,
    color: "CADCFC", margin: 0,
  });
  s.addText([
    { text: "BAAI/bge-m3", options: { bold: true, color: GOLD } },
    { text: "   ·   ", options: { color: "8794B3" } },
    { text: "ChromaDB", options: { bold: true, color: GOLD } },
    { text: "   ·   ", options: { color: "8794B3" } },
    { text: "Ollama Qwen2.5", options: { bold: true, color: GOLD } },
    { text: "   ·   ", options: { color: "8794B3" } },
    { text: "Gradio", options: { bold: true, color: GOLD } },
  ], {
    x: 0.7, y: 4.3, w: 8.5, h: 0.4,
    fontSize: 13, fontFace: BODY_FONT, color: WHITE, margin: 0,
  });
  s.addText("Báo cáo trình bày  ·  2026", {
    x: 0.7, y: H - 0.6, w: 6, h: 0.3,
    fontSize: 10, fontFace: BODY_FONT, color: "8794B3", margin: 0,
  });
}

// ============================================================
// SLIDE 2 — BỐI CẢNH & VẤN ĐỀ
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  addHeader(s, "01 · Bối cảnh", "Vì sao cần một hệ thống RAG cho hợp đồng?");

  const items = [
    {
      title: "Văn bản dài, nhiều phiên bản",
      desc: "Hợp đồng pháp lý thường được sửa qua nhiều bản v1, v2…; so sánh thủ công tốn thời gian và dễ sót.",
    },
    {
      title: "Cấu trúc chặt chẽ",
      desc: "Chương / Mục / Điều / Khoản phải được giữ đúng khi chia đoạn — không thể cắt mù theo độ dài.",
    },
    {
      title: "Dữ liệu nhạy cảm",
      desc: "Không được gửi nội dung hợp đồng ra dịch vụ cloud → mọi mô hình phải chạy cục bộ (offline).",
    },
    {
      title: "Đòi hỏi truy nguồn",
      desc: "Kết luận phải kèm trích dẫn cụ thể (file, phiên bản, điều khoản) — “không bằng chứng → không kết luận”.",
    },
  ];
  // 2x2 grid
  const startX = 0.5, startY = 1.5;
  const cw = 4.4, ch = 1.7, gap = 0.2;
  items.forEach((it, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = startX + col * (cw + gap);
    const y = startY + row * (ch + gap);
    card(s, x, y, cw, ch, PANEL);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.06, h: ch, fill: { color: GOLD }, line: { color: GOLD },
    });
    s.addText(it.title, {
      x: x + 0.25, y: y + 0.15, w: cw - 0.35, h: 0.4,
      fontSize: 15, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });
    s.addText(it.desc, {
      x: x + 0.25, y: y + 0.6, w: cw - 0.35, h: ch - 0.7,
      fontSize: 12, fontFace: BODY_FONT, color: TEXT_DARK, margin: 0, paraSpaceAfter: 4,
    });
  });

  addFooter(s, 2, 18);
}

// ============================================================
// SLIDE 3 — MỤC TIÊU & PHẠM VI
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  addHeader(s, "02 · Mục tiêu", "Hệ thống làm được gì");

  // Left: bullets
  s.addText([
    { text: "Đầu vào:  ", options: { bold: true, color: NAVY } },
    { text: "hai phiên bản DOCX của cùng một hợp đồng (v1 và v2).", options: { color: TEXT_DARK, breakLine: true } },
    { text: "Phát hiện:  ", options: { bold: true, color: NAVY } },
    { text: "các thay đổi THÊM / XOÁ / SỬA ở cấp Điều / Khoản.", options: { color: TEXT_DARK, breakLine: true } },
    { text: "Trích nguồn:  ", options: { bold: true, color: NAVY } },
    { text: "mỗi thay đổi gắn (doc_id, version, clause_id, đoạn trích).", options: { color: TEXT_DARK, breakLine: true } },
    { text: "Sinh báo cáo:  ", options: { bold: true, color: NAVY } },
    { text: "plain text + Word (.docx) + JSON.", options: { color: TEXT_DARK, breakLine: true } },
    { text: "Giao diện:  ", options: { bold: true, color: NAVY } },
    { text: "chatbot Gradio cho người dùng cuối.", options: { color: TEXT_DARK, breakLine: true } },
    { text: "Ràng buộc:  ", options: { bold: true, color: NAVY } },
    { text: "chạy hoàn toàn offline trên máy người dùng.", options: { color: TEXT_DARK } },
  ], {
    x: 0.5, y: 1.5, w: 5.6, h: 3.4,
    fontSize: 13.5, fontFace: BODY_FONT,
    paraSpaceAfter: 10, margin: 0,
  });

  // Right: callout boxes — scope in vs out
  card(s, 6.4, 1.5, 3.1, 1.55, "EAF1E4", "B9D1A8");
  s.addText("Trong phạm vi", {
    x: 6.55, y: 1.6, w: 2.9, h: 0.3,
    fontSize: 11, fontFace: BODY_FONT, bold: true, color: GREEN, charSpacing: 3, margin: 0,
  });
  s.addText("DOCX · Tiếng Việt · So sánh 2 bản · Trích nguồn · Báo cáo Word", {
    x: 6.55, y: 1.95, w: 2.9, h: 1.1,
    fontSize: 11, fontFace: BODY_FONT, color: TEXT_DARK, margin: 0,
  });

  card(s, 6.4, 3.2, 3.1, 1.55, "F7E8E6", "E0BFBA");
  s.addText("Ngoài phạm vi", {
    x: 6.55, y: 3.3, w: 2.9, h: 0.3,
    fontSize: 11, fontFace: BODY_FONT, bold: true, color: RED, charSpacing: 3, margin: 0,
  });
  s.addText("Tư vấn pháp luật · Đánh giá hợp pháp · PDF scan/OCR · So sánh > 2 bản", {
    x: 6.55, y: 3.65, w: 2.9, h: 1.1,
    fontSize: 11, fontFace: BODY_FONT, color: TEXT_DARK, margin: 0,
  });

  addFooter(s, 3, 18);
}

// ============================================================
// SLIDE 4 — PIPELINE TỔNG QUAN  (mega diagram)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  addHeader(s, "03 · Kiến trúc", "Luồng xử lý RAG end-to-end");

  // Three rows: INGEST (top), STORAGE (middle), QUERY/GENERATE (bottom)
  // Section labels left
  function band(y, h, label, color) {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 1.1, h,
      fill: { color }, line: { color },
    });
    s.addText(label, {
      x: 0.5, y, w: 1.1, h,
      fontSize: 10, fontFace: BODY_FONT, bold: true,
      color: WHITE, align: "center", valign: "middle",
      charSpacing: 3, margin: 0,
    });
  }
  band(1.4, 1.0, "INGEST", NAVY);
  band(2.55, 1.0, "STORE", MID_NAVY);
  band(3.7, 1.25, "RETRIEVE\n+ GENERATE", GOLD_DK);

  // Row 1: DOCX -> Loader -> Chunker -> Embedder
  const r1y = 1.55;
  const w1 = 1.7, h1 = 0.7;
  let x = 1.85;
  pipelineBox(s, x, r1y, w1, h1, "DOCX", "Hop_dong_*_v*.docx"); arrow(s, x + w1, r1y + h1/2, 0.25);
  x += w1 + 0.25;
  pipelineBox(s, x, r1y, w1, h1, "Loader", "python-docx · paragraphs"); arrow(s, x + w1, r1y + h1/2, 0.25);
  x += w1 + 0.25;
  pipelineBox(s, x, r1y, w1, h1, "Chunker", "Regex Điều/Chương · token fallback"); arrow(s, x + w1, r1y + h1/2, 0.25);
  x += w1 + 0.25;
  pipelineBox(s, x, r1y, w1, h1, "Embedder", "BAAI/bge-m3 · offline");

  // Row 2: ChromaDB centered
  const r2y = 2.7;
  // arrow from embedder down
  s.addShape(pres.shapes.LINE, {
    x: x + w1/2, y: r1y + h1, w: 0, h: r2y - (r1y + h1),
    line: { color: MID_NAVY, width: 2 },
  });
  // small triangle
  s.addShape(pres.shapes.RIGHT_TRIANGLE, {
    x: x + w1/2 - 0.09, y: r2y - 0.18, w: 0.18, h: 0.18,
    fill: { color: MID_NAVY }, line: { color: MID_NAVY }, rotate: 180,
  });

  // chroma box wide
  const chromaX = 1.85, chromaY = r2y, chromaW = 7.65, chromaH = 0.7;
  s.addShape(pres.shapes.RECTANGLE, {
    x: chromaX, y: chromaY, w: chromaW, h: chromaH,
    fill: { color: CREAM }, line: { color: GOLD, width: 1 },
  });
  s.addText("ChromaDB", {
    x: chromaX + 0.2, y: chromaY + 0.08, w: 2, h: 0.3,
    fontSize: 13, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
  });
  s.addText("collection: legal_contracts_collection   ·   metadata: { doc_id, version, clause_id, chunk_index, text }", {
    x: chromaX + 0.2, y: chromaY + 0.4, w: chromaW - 0.4, h: 0.3,
    fontSize: 10.5, fontFace: BODY_FONT, color: TEXT_MUTED, margin: 0,
  });

  // Row 3: Query -> Retriever -> Pairer -> LLM -> Report
  const r3y = 3.85;
  // arrow from chroma down INTO Retriever (the one that queries Chroma)
  const retrieverMid = 1.85 + 1.4 + 0.18 + 1.4 / 2; // = 4.13
  s.addShape(pres.shapes.LINE, {
    x: retrieverMid, y: chromaY + chromaH, w: 0, h: r3y - (chromaY + chromaH),
    line: { color: GOLD_DK, width: 2 },
  });
  s.addShape(pres.shapes.RIGHT_TRIANGLE, {
    x: retrieverMid - 0.09, y: r3y - 0.18, w: 0.18, h: 0.18,
    fill: { color: GOLD_DK }, line: { color: GOLD_DK }, rotate: 180,
  });

  const w3 = 1.4, h3 = 0.75;
  let xq = 1.85;
  pipelineBox(s, xq, r3y, w3, h3, "Query", "doc_id · version · clause_id"); arrow(s, xq + w3, r3y + h3/2, 0.18, GOLD_DK);
  xq += w3 + 0.18;
  pipelineBox(s, xq, r3y, w3, h3, "Retriever", "similarity + filter"); arrow(s, xq + w3, r3y + h3/2, 0.18, GOLD_DK);
  xq += w3 + 0.18;
  pipelineBox(s, xq, r3y, w3, h3, "Pairer", "ghép v1 ↔ v2"); arrow(s, xq + w3, r3y + h3/2, 0.18, GOLD_DK);
  xq += w3 + 0.18;
  pipelineBox(s, xq, r3y, w3, h3, "LLM Qwen2.5", "JSON {THÊM/XOÁ/SỬA}"); arrow(s, xq + w3, r3y + h3/2, 0.18, GOLD_DK);
  xq += w3 + 0.18;
  pipelineBox(s, xq, r3y, w3, h3, "Citation + Report", ".docx + JSON + UI");

  // Caption
  s.addText("Mỗi khối ứng với một module trong  legal_rag/  — chi tiết ở các slide tiếp theo.", {
    x: 0.5, y: 4.85, w: 9, h: 0.3,
    fontSize: 10.5, fontFace: BODY_FONT, italic: true, color: TEXT_MUTED, margin: 0,
  });

  addFooter(s, 4, 18);
}

// ============================================================
// Generic step-slide builder used for steps 5..13
// ============================================================
function stepSlide({ kicker, title, stepNum, bullets, codeLines, diagram, pageNo }) {
  const s = pres.addSlide();
  s.background = { color: WHITE };
  addHeader(s, kicker, title);

  // Step badge top-right
  stepBadge(s, W - 1.0, 0.4, stepNum);
  s.addText(`BƯỚC ${stepNum}`, {
    x: W - 2.1, y: 0.55, w: 1.05, h: 0.3,
    fontSize: 10, fontFace: BODY_FONT, bold: true, color: GOLD_DK,
    align: "right", margin: 0,
  });

  // Two-column body
  const leftX = 0.5, leftW = 5.0;
  const rightX = 5.8, rightW = 3.7;
  const topY = 1.5;

  // Left: bullet list
  const bulletItems = bullets.map((b, i) => ({
    text: b,
    options: { bullet: { code: "25A0" }, color: TEXT_DARK, breakLine: i !== bullets.length - 1 },
  }));
  s.addText(bulletItems, {
    x: leftX, y: topY, w: leftW, h: 3.0,
    fontSize: 13, fontFace: BODY_FONT,
    paraSpaceAfter: 8, margin: 0,
  });

  // Left bottom: optional code panel
  if (codeLines && codeLines.length) {
    const cy = 4.0;
    s.addShape(pres.shapes.RECTANGLE, {
      x: leftX, y: cy, w: leftW, h: 0.9,
      fill: { color: "0F172A" }, line: { color: "0F172A" },
    });
    const code = codeLines.map((l, i) => ({
      text: l,
      options: { color: "E2E8F0", breakLine: i !== codeLines.length - 1 },
    }));
    s.addText(code, {
      x: leftX + 0.15, y: cy + 0.1, w: leftW - 0.3, h: 0.7,
      fontSize: 10.5, fontFace: "Consolas", margin: 0,
    });
  }

  // Right: diagram
  if (diagram) {
    diagram(s, rightX, topY, rightW, 3.4);
  }

  addFooter(s, pageNo, 18);
  return s;
}

// ============================================================
// SLIDE 5 — INGESTION: LOADER
// ============================================================
stepSlide({
  kicker: "04 · Ingestion",
  title: "Đọc DOCX — chuẩn hoá thành paragraph",
  stepNum: 1,
  bullets: [
    "loader.py dùng python-docx để trích từng paragraph.",
    "Quy ước đặt tên file giúp suy ra metadata gốc: {doc_id}_{version}.docx",
    "Ví dụ: Hop_dong_A_v1.docx  →  doc_id = Hop_dong_A, version = v1.",
    "document_processor.py điều phối loader + chunker và gắn metadata cho từng chunk.",
  ],
  codeLines: [
    "$ python scripts/ingest.py",
    "# reset_collection() rồi nạp lại toàn bộ data/raw/*.docx",
  ],
  diagram: (s, x, y, w, h) => {
    // file -> paragraphs -> processor
    card(s, x, y, w, h, LIGHT);
    s.addText("Loader pipeline", {
      x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.3,
      fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });
    // file shape
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.4, y: y + 0.55, w: 1.0, h: 1.0,
      fill: { color: WHITE }, line: { color: NAVY, width: 1 },
    });
    s.addText("DOCX", {
      x: x + 0.4, y: y + 0.55, w: 1.0, h: 1.0,
      fontSize: 11, fontFace: BODY_FONT, bold: true,
      color: NAVY, align: "center", valign: "middle", margin: 0,
    });
    // arrow
    arrow(s, x + 1.5, y + 1.05, 0.4);
    // paragraphs
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 2.0, y: y + 0.55, w: 1.3, h: 1.0,
      fill: { color: WHITE }, line: { color: MID_NAVY, width: 1 },
    });
    s.addText("Paragraph\nstream", {
      x: x + 2.0, y: y + 0.55, w: 1.3, h: 1.0,
      fontSize: 10, fontFace: BODY_FONT,
      color: TEXT_DARK, align: "center", valign: "middle", margin: 0,
    });
    // arrow down to metadata
    s.addShape(pres.shapes.LINE, {
      x: x + w/2, y: y + 1.6, w: 0, h: 0.35,
      line: { color: GOLD_DK, width: 2 },
    });
    s.addShape(pres.shapes.RIGHT_TRIANGLE, {
      x: x + w/2 - 0.09, y: y + 1.92, w: 0.18, h: 0.18,
      fill: { color: GOLD_DK }, line: { color: GOLD_DK }, rotate: 180,
    });
    // metadata box
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.25, y: y + 2.15, w: w - 0.5, h: 1.05,
      fill: { color: CREAM }, line: { color: GOLD, width: 1 },
    });
    s.addText("Metadata gắn vào chunk", {
      x: x + 0.4, y: y + 2.2, w: w - 0.7, h: 0.3,
      fontSize: 10.5, fontFace: BODY_FONT, bold: true, color: NAVY, margin: 0,
    });
    s.addText("doc_id  ·  version  ·  clause_id  ·  chunk_index  ·  text", {
      x: x + 0.4, y: y + 2.55, w: w - 0.7, h: 0.6,
      fontSize: 10, fontFace: "Consolas", color: TEXT_DARK, margin: 0,
    });
  },
  pageNo: 5,
});

// ============================================================
// SLIDE 6 — CHUNKING
// ============================================================
stepSlide({
  kicker: "05 · Chunking",
  title: "Chia đoạn tôn trọng cấu trúc pháp lý",
  stepNum: 2,
  bullets: [
    "Ưu tiên 3 lớp regex (cao → thấp) để giữ ranh giới có nghĩa.",
    "LEGAL: bắt “Điều 1”, “Điều 2”…  →  clause_id = dieu_3.",
    "STRUCTURE: Chương / Mục / Phần làm khung cấp cao.",
    "GENERIC: heading dạng “Phạm vi điều chỉnh”, “Đối tượng áp dụng”.",
    "Fallback theo token nếu không có heading: MAX_CHUNK_TOKENS=512, overlap=64.",
  ],
  diagram: (s, x, y, w, h) => {
    card(s, x, y, w, h, LIGHT);
    s.addText("Thứ tự ưu tiên", {
      x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.3,
      fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });
    const tiers = [
      { name: "LEGAL", desc: "“Điều N …”", color: GOLD },
      { name: "STRUCTURE", desc: "Chương / Mục / Phần", color: MID_NAVY },
      { name: "GENERIC", desc: "Heading tự do", color: "5B7BA8" },
      { name: "TOKEN FALLBACK", desc: "512 tokens · overlap 64", color: TEXT_MUTED },
    ];
    let ty = y + 0.5;
    const th = 0.55;
    tiers.forEach((t, i) => {
      s.addShape(pres.shapes.RECTANGLE, {
        x: x + 0.25, y: ty, w: w - 0.5, h: th,
        fill: { color: WHITE }, line: { color: BORDER, width: 0.75 },
      });
      // colored chip
      s.addShape(pres.shapes.RECTANGLE, {
        x: x + 0.25, y: ty, w: 0.18, h: th,
        fill: { color: t.color }, line: { color: t.color },
      });
      s.addText(`${i + 1}`, {
        x: x + 0.5, y: ty, w: 0.35, h: th,
        fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY,
        align: "left", valign: "middle", margin: 0,
      });
      s.addText(t.name, {
        x: x + 0.85, y: ty, w: 1.4, h: th,
        fontSize: 11, fontFace: BODY_FONT, bold: true, color: NAVY,
        valign: "middle", margin: 0,
      });
      s.addText(t.desc, {
        x: x + 2.25, y: ty, w: w - 2.45, h: th,
        fontSize: 10, fontFace: BODY_FONT, color: TEXT_MUTED,
        valign: "middle", margin: 0,
      });
      ty += th + 0.1;
    });
  },
  pageNo: 6,
});

// ============================================================
// SLIDE 7 — EMBEDDING BGE-M3
// ============================================================
stepSlide({
  kicker: "06 · Embedding",
  title: "Vector hoá bằng BAAI/bge-m3",
  stepNum: 3,
  bullets: [
    "BAAI/bge-m3 — multilingual, hỗ trợ tiếng Việt rất tốt, context dài.",
    "Chạy offline (HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE) — không gọi mạng.",
    "DEVICE = cuda nếu USE_GPU=1, ngược lại fallback CPU.",
    "BGEEmbeddingModel encode batch các chunk thành dense vector.",
  ],
  codeLines: [
    "EMBEDDING_MODEL_NAME = 'BAAI/bge-m3'",
    "DEVICE = 'cuda' if os.environ.get('USE_GPU') == '1' else 'cpu'",
  ],
  diagram: (s, x, y, w, h) => {
    card(s, x, y, w, h, LIGHT);
    s.addText("text  →  vector", {
      x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.3,
      fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });
    // chunk box
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.25, y: y + 0.55, w: 1.5, h: 1.0,
      fill: { color: WHITE }, line: { color: BORDER, width: 0.75 },
    });
    s.addText("“Điều 3. Giá\nhợp đồng…”", {
      x: x + 0.3, y: y + 0.6, w: 1.4, h: 0.9,
      fontSize: 10, fontFace: BODY_FONT, italic: true,
      color: TEXT_DARK, valign: "middle", margin: 0,
    });
    arrow(s, x + 1.8, y + 1.05, 0.3);
    // encoder
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: x + 2.15, y: y + 0.7, w: 1.3, h: 0.7,
      fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.1,
    });
    s.addText("bge-m3", {
      x: x + 2.15, y: y + 0.7, w: 1.3, h: 0.7,
      fontSize: 12, fontFace: HEAD_FONT, bold: true,
      color: GOLD, align: "center", valign: "middle", margin: 0,
    });

    // arrow down
    s.addShape(pres.shapes.LINE, {
      x: x + w/2, y: y + 1.65, w: 0, h: 0.35,
      line: { color: GOLD_DK, width: 2 },
    });
    s.addShape(pres.shapes.RIGHT_TRIANGLE, {
      x: x + w/2 - 0.09, y: y + 1.98, w: 0.18, h: 0.18,
      fill: { color: GOLD_DK }, line: { color: GOLD_DK }, rotate: 180,
    });

    // vector visual
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.25, y: y + 2.25, w: w - 0.5, h: 0.95,
      fill: { color: CREAM }, line: { color: GOLD, width: 1 },
    });
    s.addText("[ 0.12,  -0.03,  0.81,  …,  0.07 ]", {
      x: x + 0.25, y: y + 2.25, w: w - 0.5, h: 0.5,
      fontSize: 11, fontFace: "Consolas", bold: true, color: NAVY,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText("dense vector  ·  multilingual", {
      x: x + 0.25, y: y + 2.7, w: w - 0.5, h: 0.4,
      fontSize: 10, fontFace: BODY_FONT, italic: true,
      color: TEXT_MUTED, align: "center", margin: 0,
    });
  },
  pageNo: 7,
});

// ============================================================
// SLIDE 8 — VECTOR STORE
// ============================================================
stepSlide({
  kicker: "07 · Vector Store",
  title: "Lưu vào ChromaDB cục bộ",
  stepNum: 4,
  bullets: [
    "ChromaDB persistent client trỏ vào data/chroma_db/.",
    "Một collection duy nhất: legal_contracts_collection.",
    "Mỗi chunk lưu kèm metadata để lọc nhanh.",
    "scripts/ingest.py gọi reset_collection() trước  →  nạp lại từ đầu, tránh trùng.",
    "scripts/view_chunks.py để soi dữ liệu đã nạp (--stats, --doc-id, --version).",
  ],
  diagram: (s, x, y, w, h) => {
    card(s, x, y, w, h, LIGHT);
    s.addText("Metadata schema", {
      x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.3,
      fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });
    const rows = [
      ["doc_id",      "Hop_dong_A"],
      ["version",     "v1 | v2"],
      ["clause_id",   "dieu_3"],
      ["chunk_index", "0, 1, 2 …"],
      ["text",        "nội dung gốc"],
    ];
    let ry = y + 0.5;
    rows.forEach((r, i) => {
      const bg = i % 2 === 0 ? WHITE : LIGHT;
      s.addShape(pres.shapes.RECTANGLE, {
        x: x + 0.25, y: ry, w: w - 0.5, h: 0.42,
        fill: { color: bg }, line: { color: BORDER, width: 0.5 },
      });
      s.addText(r[0], {
        x: x + 0.35, y: ry, w: 1.4, h: 0.42,
        fontSize: 11, fontFace: "Consolas", bold: true, color: NAVY,
        valign: "middle", margin: 0,
      });
      s.addText(r[1], {
        x: x + 1.75, y: ry, w: w - 2.0, h: 0.42,
        fontSize: 10.5, fontFace: BODY_FONT, color: TEXT_DARK,
        valign: "middle", margin: 0,
      });
      ry += 0.45;
    });
  },
  pageNo: 8,
});

// ============================================================
// SLIDE 9 — RETRIEVAL
// ============================================================
stepSlide({
  kicker: "08 · Retrieval",
  title: "Tìm kiếm ngữ nghĩa + bộ lọc metadata",
  stepNum: 5,
  bullets: [
    "LegalRetriever.search(query, doc_id=, version=, clause_id=, k=) — kết hợp similarity và filter.",
    "k=20 mặc định cho luồng so sánh để đủ ngữ cảnh.",
    "Filter giúp giới hạn đúng hợp đồng / phiên bản / điều khoản mong muốn.",
    "Có thể chạy độc lập qua CLI để debug truy vấn.",
  ],
  codeLines: [
    "$ python scripts/search.py \"Quy dinh thanh toan\" -k 5 \\",
    "      --doc-id Hop_dong_A --version v1",
  ],
  diagram: (s, x, y, w, h) => {
    card(s, x, y, w, h, LIGHT);
    s.addText("Luồng truy vấn", {
      x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.3,
      fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });
    // Query
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: x + 0.25, y: y + 0.55, w: w - 0.5, h: 0.5,
      fill: { color: WHITE }, line: { color: MID_NAVY, width: 1 }, rectRadius: 0.08,
    });
    s.addText("Query  +  filters {doc_id, version}", {
      x: x + 0.25, y: y + 0.55, w: w - 0.5, h: 0.5,
      fontSize: 11, fontFace: BODY_FONT, color: TEXT_DARK,
      align: "center", valign: "middle", margin: 0,
    });
    // arrow
    s.addShape(pres.shapes.LINE, {
      x: x + w/2, y: y + 1.1, w: 0, h: 0.3,
      line: { color: MID_NAVY, width: 2 },
    });
    s.addShape(pres.shapes.RIGHT_TRIANGLE, {
      x: x + w/2 - 0.09, y: y + 1.38, w: 0.18, h: 0.18,
      fill: { color: MID_NAVY }, line: { color: MID_NAVY }, rotate: 180,
    });
    // chroma
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.25, y: y + 1.6, w: w - 0.5, h: 0.55,
      fill: { color: CREAM }, line: { color: GOLD, width: 1 },
    });
    s.addText("ChromaDB  ·  cosine + where{…}", {
      x: x + 0.25, y: y + 1.6, w: w - 0.5, h: 0.55,
      fontSize: 11, fontFace: BODY_FONT, bold: true, color: NAVY,
      align: "center", valign: "middle", margin: 0,
    });
    // arrow
    s.addShape(pres.shapes.LINE, {
      x: x + w/2, y: y + 2.2, w: 0, h: 0.3,
      line: { color: GOLD_DK, width: 2 },
    });
    s.addShape(pres.shapes.RIGHT_TRIANGLE, {
      x: x + w/2 - 0.09, y: y + 2.48, w: 0.18, h: 0.18,
      fill: { color: GOLD_DK }, line: { color: GOLD_DK }, rotate: 180,
    });
    // top-k chunks
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.25, y: y + 2.7, w: w - 0.5, h: 0.6,
      fill: { color: WHITE }, line: { color: BORDER, width: 1 },
    });
    s.addText("Top-k chunks  (k = 20 cho compare)", {
      x: x + 0.25, y: y + 2.7, w: w - 0.5, h: 0.6,
      fontSize: 11, fontFace: BODY_FONT, color: NAVY,
      align: "center", valign: "middle", margin: 0,
    });
  },
  pageNo: 9,
});

// ============================================================
// SLIDE 10 — CONTEXT PAIRING
// ============================================================
stepSlide({
  kicker: "09 · Context Pairing",
  title: "Ghép cặp điều khoản v1 ↔ v2",
  stepNum: 6,
  bullets: [
    "ContextPairer ghép chunk bản cũ và bản mới theo clause_id chung.",
    "Đảm bảo LLM so sánh đúng điều khoản tương ứng, không lệch ngữ cảnh.",
    "Chunk lẻ (chỉ có ở một bên) được đánh dấu là THÊM hoặc XOÁ ở cấp điều khoản.",
    "Chạy thử: python scripts/search.py \"…\" --clause-id dieu_3 --pair",
  ],
  diagram: (s, x, y, w, h) => {
    card(s, x, y, w, h, LIGHT);
    s.addText("Pairing theo clause_id", {
      x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.3,
      fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });

    // two columns of chunk chips
    const colW = 1.3;
    const oldX = x + 0.25, newX = x + w - 0.25 - colW;
    s.addText("v1", {
      x: oldX, y: y + 0.5, w: colW, h: 0.3,
      fontSize: 11, fontFace: BODY_FONT, bold: true, color: MID_NAVY,
      align: "center", margin: 0,
    });
    s.addText("v2", {
      x: newX, y: y + 0.5, w: colW, h: 0.3,
      fontSize: 11, fontFace: BODY_FONT, bold: true, color: GOLD_DK,
      align: "center", margin: 0,
    });
    const labels = ["dieu_1", "dieu_2", "dieu_3", "dieu_5"];
    let cy = y + 0.85;
    labels.forEach((lab) => {
      s.addShape(pres.shapes.RECTANGLE, {
        x: oldX, y: cy, w: colW, h: 0.4,
        fill: { color: WHITE }, line: { color: MID_NAVY, width: 0.75 },
      });
      s.addText(lab, {
        x: oldX, y: cy, w: colW, h: 0.4,
        fontSize: 10, fontFace: "Consolas", color: NAVY,
        align: "center", valign: "middle", margin: 0,
      });
      s.addShape(pres.shapes.RECTANGLE, {
        x: newX, y: cy, w: colW, h: 0.4,
        fill: { color: WHITE }, line: { color: GOLD, width: 0.75 },
      });
      s.addText(lab, {
        x: newX, y: cy, w: colW, h: 0.4,
        fontSize: 10, fontFace: "Consolas", color: NAVY,
        align: "center", valign: "middle", margin: 0,
      });
      // link line
      s.addShape(pres.shapes.LINE, {
        x: oldX + colW, y: cy + 0.2, w: newX - (oldX + colW), h: 0,
        line: { color: GOLD, width: 1.5, dashType: "dash" },
      });
      cy += 0.5;
    });
    s.addText("Mỗi cặp được gửi tới LLM để mô tả thay đổi.", {
      x: x + 0.25, y: y + h - 0.45, w: w - 0.5, h: 0.3,
      fontSize: 9.5, fontFace: BODY_FONT, italic: true, color: TEXT_MUTED,
      align: "center", margin: 0,
    });
  },
  pageNo: 10,
});

// ============================================================
// SLIDE 11 — GENERATION
// ============================================================
stepSlide({
  kicker: "10 · Generation",
  title: "LLM Comparator — Ollama Qwen2.5",
  stepNum: 7,
  bullets: [
    "DocumentComparator gọi Ollama tại http://localhost:11434.",
    "Model qwen2.5:1.5b — đủ để chạy CPU/GPU local.",
    "Temperature = 0.0  →  output ổn định, deterministic.",
    "num_ctx = 2048, max_tokens = 768  →  KV cache nhỏ, tránh loop.",
    "Output mỗi cặp là JSON chuẩn: {THÊM, XOÁ, SỬA}.",
  ],
  diagram: (s, x, y, w, h) => {
    card(s, x, y, w, h, LIGHT);
    s.addText("JSON schema mong đợi", {
      x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.3,
      fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.2, y: y + 0.5, w: w - 0.4, h: 2.75,
      fill: { color: "0F172A" }, line: { color: "0F172A" },
    });
    const code = [
      "{",
      "  \"changes\": [",
      "    {",
      "      \"type\": \"SỬA\",",
      "      \"old_text\": \"30%\",",
      "      \"new_text\": \"40%\",",
      "      \"location\": \"Khoản 2.1\"",
      "    }",
      "  ]",
      "}",
    ];
    s.addText(code.map((l, i) => ({
      text: l,
      options: { color: i === 3 ? GOLD : "E2E8F0", breakLine: i !== code.length - 1, bold: i === 3 },
    })), {
      x: x + 0.35, y: y + 0.6, w: w - 0.7, h: 2.6,
      fontSize: 10.5, fontFace: "Consolas", margin: 0,
    });
  },
  pageNo: 11,
});

// ============================================================
// SLIDE 12 — CITATION
// ============================================================
stepSlide({
  kicker: "11 · Citation",
  title: "Gắn nguồn cho từng thay đổi",
  stepNum: 8,
  bullets: [
    "CitationMapper (legal_rag/generation/citation.py) tra ngược chunk gốc.",
    "Mỗi change được enrich: (doc_id, version, clause_id, đoạn trích nguyên văn).",
    "Tăng tính kiểm chứng: người đọc có thể quay về vị trí gốc trong DOCX.",
    "Quy tắc: nếu không tìm thấy bằng chứng  →  loại bỏ thay đổi đó.",
  ],
  diagram: (s, x, y, w, h) => {
    card(s, x, y, w, h, LIGHT);
    s.addText("Trước  →  Sau citation", {
      x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.3,
      fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });
    // before
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.2, y: y + 0.5, w: w - 0.4, h: 1.0,
      fill: { color: WHITE }, line: { color: BORDER, width: 0.75 },
    });
    s.addText("SỬA  30%  →  40%", {
      x: x + 0.35, y: y + 0.55, w: w - 0.7, h: 0.4,
      fontSize: 11, fontFace: BODY_FONT, bold: true, color: NAVY, margin: 0,
    });
    s.addText("(thiếu nguồn)", {
      x: x + 0.35, y: y + 0.95, w: w - 0.7, h: 0.4,
      fontSize: 10, fontFace: BODY_FONT, italic: true, color: RED, margin: 0,
    });
    // arrow down
    s.addShape(pres.shapes.LINE, {
      x: x + w/2, y: y + 1.55, w: 0, h: 0.3,
      line: { color: GOLD_DK, width: 2 },
    });
    s.addShape(pres.shapes.RIGHT_TRIANGLE, {
      x: x + w/2 - 0.09, y: y + 1.83, w: 0.18, h: 0.18,
      fill: { color: GOLD_DK }, line: { color: GOLD_DK }, rotate: 180,
    });
    // after
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.2, y: y + 2.1, w: w - 0.4, h: 1.2,
      fill: { color: CREAM }, line: { color: GOLD, width: 1 },
    });
    s.addText("SỬA  30%  →  40%", {
      x: x + 0.35, y: y + 2.15, w: w - 0.7, h: 0.35,
      fontSize: 11, fontFace: BODY_FONT, bold: true, color: NAVY, margin: 0,
    });
    s.addText("Hop_dong_A · v2 · dieu_3", {
      x: x + 0.35, y: y + 2.5, w: w - 0.7, h: 0.3,
      fontSize: 10, fontFace: "Consolas", color: GOLD_DK, margin: 0,
    });
    s.addText("“… tạm ứng 40% giá trị hợp đồng …”", {
      x: x + 0.35, y: y + 2.8, w: w - 0.7, h: 0.4,
      fontSize: 10, fontFace: BODY_FONT, italic: true, color: TEXT_DARK, margin: 0,
    });
  },
  pageNo: 12,
});

// ============================================================
// SLIDE 13 — REPORT
// ============================================================
stepSlide({
  kicker: "12 · Report",
  title: "Sinh báo cáo — Plain text · JSON · Word",
  stepNum: 9,
  bullets: [
    "ReportGenerator dùng LLM để viết tóm tắt; có fallback rule-based nếu Ollama không sẵn sàng.",
    "generate_word_report.py xuất .docx có heading + bảng thay đổi.",
    "Snapshot trung gian: output/report_data.json — tái sử dụng cho UI/Word report.",
    "scripts/compare.py chạy đầu-đến-cuối: compare → citation → report.",
  ],
  codeLines: [
    "$ python scripts/compare.py --doc-id Hop_dong_A --old v1 --new v2 --json",
    "$ python scripts/generate_word_report.py --from-json output/report_data.json",
  ],
  diagram: (s, x, y, w, h) => {
    card(s, x, y, w, h, LIGHT);
    s.addText("Output formats", {
      x: x + 0.15, y: y + 0.1, w: w - 0.3, h: 0.3,
      fontSize: 12, fontFace: HEAD_FONT, bold: true, color: NAVY, margin: 0,
    });
    const fmts = [
      { ext: ".docx", desc: "Báo cáo cho người dùng cuối" },
      { ext: ".json", desc: "Snapshot cấu trúc thay đổi" },
      { ext: ".txt",  desc: "Plain text tóm tắt nhanh" },
    ];
    let fy = y + 0.55;
    fmts.forEach((f) => {
      s.addShape(pres.shapes.RECTANGLE, {
        x: x + 0.25, y: fy, w: w - 0.5, h: 0.75,
        fill: { color: WHITE }, line: { color: BORDER, width: 0.75 },
      });
      // tag
      s.addShape(pres.shapes.RECTANGLE, {
        x: x + 0.25, y: fy, w: 0.95, h: 0.75,
        fill: { color: NAVY }, line: { color: NAVY },
      });
      s.addText(f.ext, {
        x: x + 0.25, y: fy, w: 0.95, h: 0.75,
        fontSize: 13, fontFace: HEAD_FONT, bold: true,
        color: GOLD, align: "center", valign: "middle", margin: 0,
      });
      s.addText(f.desc, {
        x: x + 1.3, y: fy, w: w - 1.55, h: 0.75,
        fontSize: 11, fontFace: BODY_FONT, color: TEXT_DARK,
        valign: "middle", margin: 0,
      });
      fy += 0.85;
    });
  },
  pageNo: 13,
});

// ============================================================
// SLIDE 14 — GUARDRAILS
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  addHeader(s, "13 · Guardrails", "Nguyên tắc: không bằng chứng → không kết luận");

  // 3 columns of rules
  const cols = [
    {
      title: "Không tư vấn",
      desc: "Hệ thống không đưa ra lời khuyên pháp lý, không bình luận hậu quả của thay đổi.",
      color: NAVY,
    },
    {
      title: "Không phán xét",
      desc: "Không đánh giá tính hợp pháp / hợp lệ của điều khoản — chỉ mô tả khác biệt.",
      color: MID_NAVY,
    },
    {
      title: "Bám sát nguồn",
      desc: "Mọi thay đổi phải có cụm từ xuất hiện y nguyên trong văn bản; banned phrases bị chặn hậu kiểm.",
      color: GOLD_DK,
    },
  ];
  const sx = 0.5, sy = 1.55, cw = 3.0, ch = 1.9, gap = 0.2;
  cols.forEach((c, i) => {
    const x = sx + i * (cw + gap);
    card(s, x, sy, cw, ch, PANEL);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: sy, w: cw, h: 0.5,
      fill: { color: c.color }, line: { color: c.color },
    });
    s.addText(c.title, {
      x: x + 0.2, y: sy, w: cw - 0.4, h: 0.5,
      fontSize: 14, fontFace: HEAD_FONT, bold: true,
      color: GOLD, valign: "middle", margin: 0,
    });
    s.addText(c.desc, {
      x: x + 0.2, y: sy + 0.65, w: cw - 0.4, h: ch - 0.75,
      fontSize: 12, fontFace: BODY_FONT, color: TEXT_DARK, margin: 0,
    });
  });

  // Bottom: enforcement strip
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.7, w: 9.0, h: 1.0,
    fill: { color: CREAM }, line: { color: GOLD, width: 1 },
  });
  s.addText("Cơ chế thực thi", {
    x: 0.7, y: 3.75, w: 4, h: 0.3,
    fontSize: 11, fontFace: BODY_FONT, bold: true, color: GOLD_DK,
    charSpacing: 3, margin: 0,
  });
  s.addText([
    { text: "SYSTEM_PROMPT  ", options: { bold: true, color: NAVY } },
    { text: "ép schema · ", options: { color: TEXT_DARK } },
    { text: "temperature = 0.0  ", options: { bold: true, color: NAVY } },
    { text: "loại bỏ ngẫu nhiên · ", options: { color: TEXT_DARK } },
    { text: "banned phrases  ", options: { bold: true, color: NAVY } },
    { text: "lọc hậu sinh · ", options: { color: TEXT_DARK } },
    { text: "CitationMapper  ", options: { bold: true, color: NAVY } },
    { text: "loại change không có nguồn.", options: { color: TEXT_DARK } },
  ], {
    x: 0.7, y: 4.05, w: 8.6, h: 0.65,
    fontSize: 12, fontFace: BODY_FONT, margin: 0,
  });

  addFooter(s, 14, 18);
}

// ============================================================
// SLIDE 15 — EVALUATION
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  addHeader(s, "14 · Evaluation", "Ba chỉ số đánh giá chất lượng");

  const metrics = [
    {
      name: "Citation accuracy",
      value: "% thay đổi có trích dẫn",
      desc: "Kiểm tra cụm từ trong change có thật sự xuất hiện ở chunk nguồn không.",
      color: GOLD,
    },
    {
      name: "Change detection rate",
      value: "recall trên ground truth",
      desc: "So với dữ liệu chuẩn ở data/ground_truth/ — bắt được bao nhiêu thay đổi thực.",
      color: MID_NAVY,
    },
    {
      name: "Guardrail compliance",
      value: "% output đúng quy tắc",
      desc: "Output không vi phạm banned phrases, không đưa kết luận pháp lý.",
      color: NAVY,
    },
  ];
  const sx = 0.5, sy = 1.5, cw = 3.0, ch = 2.4, gap = 0.2;
  metrics.forEach((m, i) => {
    const x = sx + i * (cw + gap);
    card(s, x, sy, cw, ch);
    s.addShape(pres.shapes.OVAL, {
      x: x + cw/2 - 0.45, y: sy + 0.2, w: 0.9, h: 0.9,
      fill: { color: m.color }, line: { color: m.color },
    });
    s.addText(String(i + 1), {
      x: x + cw/2 - 0.45, y: sy + 0.2, w: 0.9, h: 0.9,
      fontSize: 28, fontFace: HEAD_FONT, bold: true,
      color: WHITE, align: "center", valign: "middle", margin: 0,
    });
    s.addText(m.name, {
      x: x + 0.15, y: sy + 1.2, w: cw - 0.3, h: 0.35,
      fontSize: 14, fontFace: HEAD_FONT, bold: true, color: NAVY,
      align: "center", margin: 0,
    });
    s.addText(m.value, {
      x: x + 0.15, y: sy + 1.55, w: cw - 0.3, h: 0.3,
      fontSize: 10, fontFace: BODY_FONT, italic: true, color: GOLD_DK,
      align: "center", charSpacing: 1, margin: 0,
    });
    s.addText(m.desc, {
      x: x + 0.2, y: sy + 1.9, w: cw - 0.4, h: ch - 2.0,
      fontSize: 11, fontFace: BODY_FONT, color: TEXT_DARK,
      align: "center", margin: 0,
    });
  });

  // CLI strip
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.2, w: 9.0, h: 0.75,
    fill: { color: "0F172A" }, line: { color: "0F172A" },
  });
  s.addText([
    { text: "$ python scripts/evaluate.py --json     ", options: { color: GOLD, breakLine: true } },
    { text: "$ python scripts/run_evaluation.py --k 20 --doc-ids Hop_dong_A", options: { color: "E2E8F0" } },
  ], {
    x: 0.7, y: 4.25, w: 8.6, h: 0.65,
    fontSize: 11, fontFace: "Consolas", margin: 0,
  });

  addFooter(s, 15, 18);
}

// ============================================================
// SLIDE 16 — UI CHATBOT
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  addHeader(s, "15 · UI", "Chatbot Gradio cho người dùng cuối");

  // Left: bullets
  s.addText([
    { text: "app.py  ", options: { bold: true, color: NAVY } },
    { text: "khởi chạy giao diện chat dựa trên Gradio.", options: { color: TEXT_DARK, breakLine: true } },
    { text: "Người dùng chọn ", options: { color: TEXT_DARK } },
    { text: "doc_id ", options: { bold: true, color: NAVY } },
    { text: "+ ", options: { color: TEXT_DARK } },
    { text: "version, ", options: { bold: true, color: NAVY } },
    { text: "đặt câu hỏi hoặc yêu cầu so sánh.", options: { color: TEXT_DARK, breakLine: true } },
    { text: "Bot gọi đúng pipeline RAG ở backend và trả lời cùng trích dẫn.", options: { color: TEXT_DARK, breakLine: true } },
    { text: "Có nút tải về báo cáo Word đã sinh.", options: { color: TEXT_DARK } },
  ], {
    x: 0.5, y: 1.5, w: 4.5, h: 3.0,
    fontSize: 13, fontFace: BODY_FONT,
    paraSpaceAfter: 8, margin: 0,
  });

  // Right: mock chatbot frame
  const fx = 5.4, fy = 1.5, fw = 4.1, fh = 3.3;
  s.addShape(pres.shapes.RECTANGLE, {
    x: fx, y: fy, w: fw, h: fh,
    fill: { color: PANEL }, line: { color: BORDER, width: 1 },
    shadow: { type: "outer", color: "000000", blur: 8, offset: 2, angle: 90, opacity: 0.15 },
  });
  // browser bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: fx, y: fy, w: fw, h: 0.35,
    fill: { color: "1F2937" }, line: { color: "1F2937" },
  });
  ["FF5F56", "FFBD2E", "27C93F"].forEach((c, i) => {
    s.addShape(pres.shapes.OVAL, {
      x: fx + 0.1 + i * 0.18, y: fy + 0.1, w: 0.13, h: 0.13,
      fill: { color: c }, line: { color: c },
    });
  });
  s.addText("Legal RAG  ·  Chatbot", {
    x: fx + 0.8, y: fy + 0.05, w: fw - 1, h: 0.25,
    fontSize: 9.5, fontFace: BODY_FONT, color: "E2E8F0", margin: 0,
  });
  // user bubble (right)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: fx + 1.4, y: fy + 0.55, w: fw - 1.6, h: 0.55,
    fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.08,
  });
  s.addText("So sánh Hop_dong_A v1 và v2", {
    x: fx + 1.5, y: fy + 0.55, w: fw - 1.8, h: 0.55,
    fontSize: 11, fontFace: BODY_FONT, color: WHITE,
    align: "right", valign: "middle", margin: 0,
  });
  // bot bubble (left)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: fx + 0.2, y: fy + 1.3, w: fw - 1.6, h: 1.65,
    fill: { color: CREAM }, line: { color: GOLD, width: 0.75 }, rectRadius: 0.08,
  });
  s.addText([
    { text: "Phát hiện 3 thay đổi:", options: { bold: true, color: NAVY, breakLine: true } },
    { text: "• SỬA 30% → 40% (Điều 3, Khoản 2.1)", options: { color: TEXT_DARK, breakLine: true } },
    { text: "• THÊM “bảo lãnh ngân hàng” (Điều 5)", options: { color: TEXT_DARK, breakLine: true } },
    { text: "• XOÁ phụ lục B (Điều 9)", options: { color: TEXT_DARK, breakLine: true } },
    { text: "Tải báo cáo: ", options: { color: TEXT_DARK } },
    { text: "bao_cao_Hop_dong_A.docx", options: { color: GOLD_DK, bold: true } },
  ], {
    x: fx + 0.35, y: fy + 1.35, w: fw - 1.85, h: 1.55,
    fontSize: 10.5, fontFace: BODY_FONT, margin: 0, paraSpaceAfter: 2,
  });

  addFooter(s, 16, 18);
}

// ============================================================
// SLIDE 17 — TECH STACK
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  addHeader(s, "16 · Stack", "Công nghệ sử dụng");

  const stack = [
    { name: "Python 3",        role: "Ngôn ngữ chính" },
    { name: "python-docx",     role: "Đọc DOCX paragraph" },
    { name: "BAAI/bge-m3",     role: "Embedding đa ngữ" },
    { name: "ChromaDB",        role: "Vector store cục bộ" },
    { name: "Ollama · Qwen2.5",role: "LLM local generation" },
    { name: "Gradio",          role: "UI chatbot" },
  ];
  const sx = 0.5, sy = 1.55, cw = 3.0, ch = 1.45, gap = 0.2;
  stack.forEach((it, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = sx + col * (cw + gap);
    const y = sy + row * (ch + gap);
    card(s, x, y, cw, ch, PANEL);
    // big initial in gold circle
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.2, y: y + 0.3, w: 0.85, h: 0.85,
      fill: { color: NAVY }, line: { color: GOLD, width: 1.5 },
    });
    s.addText(it.name.charAt(0), {
      x: x + 0.2, y: y + 0.3, w: 0.85, h: 0.85,
      fontSize: 22, fontFace: HEAD_FONT, bold: true,
      color: GOLD, align: "center", valign: "middle", margin: 0,
    });
    s.addText(it.name, {
      x: x + 1.2, y: y + 0.3, w: cw - 1.3, h: 0.4,
      fontSize: 13, fontFace: HEAD_FONT, bold: true, color: NAVY,
      valign: "bottom", margin: 0,
    });
    s.addText(it.role, {
      x: x + 1.2, y: y + 0.7, w: cw - 1.3, h: 0.5,
      fontSize: 11, fontFace: BODY_FONT, color: TEXT_MUTED,
      valign: "top", margin: 0,
    });
  });

  addFooter(s, 17, 18);
}

// ============================================================
// SLIDE 18 — KẾT LUẬN
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  // gold left bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.25, h: H, fill: { color: GOLD }, line: { color: GOLD },
  });
  s.addText("KẾT LUẬN", {
    x: 0.7, y: 0.6, w: 6, h: 0.4,
    fontSize: 12, fontFace: BODY_FONT, bold: true, color: GOLD, charSpacing: 6, margin: 0,
  });
  s.addText("Pipeline RAG cục bộ hoàn chỉnh", {
    x: 0.7, y: 1.05, w: 9, h: 0.8,
    fontSize: 30, fontFace: HEAD_FONT, bold: true, color: WHITE, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 1.85, w: 0.6, h: 0.04,
    fill: { color: GOLD }, line: { color: GOLD },
  });

  // Two columns
  const col1X = 0.7, col2X = 5.2, colW = 4.2, colY = 2.1;
  // done col
  s.addText("ĐÃ LÀM ĐƯỢC", {
    x: col1X, y: colY, w: colW, h: 0.3,
    fontSize: 11, fontFace: BODY_FONT, bold: true,
    color: GOLD, charSpacing: 4, margin: 0,
  });
  s.addText([
    { text: "Ingest → Chunk theo cấu trúc pháp lý → Embed → Chroma.", options: { color: WHITE, bullet: { code: "25A0" }, breakLine: true } },
    { text: "Retrieval có filter, pairing v1↔v2 theo clause_id.", options: { color: WHITE, bullet: { code: "25A0" }, breakLine: true } },
    { text: "LLM Qwen2.5 sinh JSON thay đổi, gắn citation.", options: { color: WHITE, bullet: { code: "25A0" }, breakLine: true } },
    { text: "Báo cáo .docx + UI Gradio + 3 metric đánh giá.", options: { color: WHITE, bullet: { code: "25A0" } } },
  ], {
    x: col1X, y: colY + 0.35, w: colW, h: 2.5,
    fontSize: 12, fontFace: BODY_FONT,
    paraSpaceAfter: 6, margin: 0,
  });

  // future col
  s.addText("HƯỚNG PHÁT TRIỂN", {
    x: col2X, y: colY, w: colW, h: 0.3,
    fontSize: 11, fontFace: BODY_FONT, bold: true,
    color: GOLD, charSpacing: 4, margin: 0,
  });
  s.addText([
    { text: "Hỗ trợ PDF scan + OCR cho hợp đồng giấy.", options: { color: WHITE, bullet: { code: "25A0" }, breakLine: true } },
    { text: "Hybrid retrieval: BM25 + dense để tăng recall.", options: { color: WHITE, bullet: { code: "25A0" }, breakLine: true } },
    { text: "Nâng LLM lên qwen2.5:7b khi có GPU; thêm self-check.", options: { color: WHITE, bullet: { code: "25A0" }, breakLine: true } },
    { text: "So sánh nhiều hơn 2 phiên bản trong cùng một báo cáo.", options: { color: WHITE, bullet: { code: "25A0" } } },
  ], {
    x: col2X, y: colY + 0.35, w: colW, h: 2.5,
    fontSize: 12, fontFace: BODY_FONT,
    paraSpaceAfter: 6, margin: 0,
  });

  // bottom thank you
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 4.6, w: 8.6, h: 0.55,
    fill: { color: NAVY }, line: { color: GOLD, width: 0.75 },
  });
  s.addText("Cảm ơn quý thầy cô và mọi người đã lắng nghe  ·  Q & A", {
    x: 0.7, y: 4.6, w: 8.6, h: 0.55,
    fontSize: 14, fontFace: HEAD_FONT, italic: true,
    color: GOLD, align: "center", valign: "middle", margin: 0,
  });
}

// ============================================================
pres.writeFile({ fileName: "Legal_RAG_Presentation.pptx" })
  .then((fn) => console.log("Wrote", fn));
