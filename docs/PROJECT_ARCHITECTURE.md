# Project Architecture Specification
## Desktop-Controlled Web-Based Document Scanner with Mobile Camera Streaming

---

## 1. Project Intent and Problem Statement

This project aims to build a self-hosted, local-first web application that replicates the functional capabilities of CamScanner while shifting control to a desktop web interface and using a smartphone purely as a wireless camera device.

The system must allow a desktop user to view a live camera feed from a smartphone or webcam, capture high-resolution document images using mouse input, apply automatic document edge detection and enhancement, perform batch editing, assemble multi-page PDFs, optionally run OCR, and share results locally or via temporary links.

This is not a mobile app, not a SaaS platform, and not a cloud-dependent service. The entire system must be deployable on a personal machine or private server and operate without user accounts or authentication.

---

## 2. Non-Negotiable Constraints

- No login system, user accounts, or identity management
- No mandatory cloud services or third-party APIs
- Smartphone acts only as a camera sensor, never as a processing node
- Desktop browser is the primary control surface
- All image processing happens server-side
- Application must work on a local network
- All enhancements must be non-destructive until export
- Privacy is enforced by architecture, not policy

Any design or implementation proposal that violates these constraints must be rejected.

---

## 3. High-Level System Overview

The system consists of three actors:

1. Desktop user operating a browser-based scanning interface
2. Smartphone browser acting as a camera streaming endpoint
3. Local server running a Flask-based backend coordinating all logic

The desktop browser renders the full scanning UI and controls capture, processing, and export. The smartphone connects via a QR-code-initiated session and streams camera data. The server orchestrates streaming, processing, document state, and file generation.

---

## 4. Subsystem Decomposition

The system is decomposed into the following stable subsystems:

### 4.1 Desktop Web Interface
Owns user interaction, live preview rendering, capture controls, enhancement controls, page management, and export actions.

### 4.2 Mobile Camera Ingress
Owns camera permission handling, video frame acquisition, and transmission to the server. Maintains no persistent state.

### 4.3 Streaming and Capture Pipeline
Owns live preview transport, capture triggering, and delivery of high-resolution still images.

### 4.4 Image Processing Engine
Owns document detection, perspective correction, illumination normalization, filtering, and optional OCR.

### 4.5 Document Session Manager
Owns multi-page document state, processing parameters, ordering, and metadata.

### 4.6 Export and Sharing Module
Owns PDF assembly, compression, text layer embedding, file storage, and temporary sharing links.

Subsystems must communicate through explicit interfaces and must not directly manipulate each other’s internal state.

---

## 5. Data Flow and State Lifetime

Live preview frames are ephemeral and must never be persisted.

Captured images become part of a document session and must be preserved in original form. All processing outputs are derived artifacts that can be regenerated.

OCR text is metadata attached to pages, not baked into images.

Final exports are generated on demand and stored separately from working session data.

---

## 6. Pairing and Session Control

The server generates a QR code containing a short-lived session token.

Scanning the QR code opens a minimal capture page on the smartphone, which establishes a streaming connection to the server.

The phone holds no authoritative state. Reconnecting or rescanning must not corrupt or reset the desktop document session.

Sessions are server-owned and time-bounded.

---

## 7. Streaming and Capture Strategy

Live preview and still capture are decoupled.

Preview frames may be lower resolution and optimized for latency.

Still capture must request a high-resolution frame directly from the camera source, independent of the preview stream.

WebRTC is the preferred streaming mechanism. A simpler fallback may exist but must be explicitly acknowledged as a tradeoff.

---

## 8. Image Processing Pipeline

The image processing pipeline consists of deterministic, reversible stages:

1. Document edge detection
2. Perspective correction and flattening
3. Illumination and shadow normalization
4. Color enhancement and filtering
5. Optional OCR

The original image must always be preserved. Processing parameters must be stored separately so batch reprocessing is possible.

---

## 9. Document Session and Batch Editing Model

A document session represents a collection of pages and associated processing parameters.

Batch edits operate on processing parameters, not destructively on images.

Page reordering, deletion, and reprocessing must not require re-capture.

---

## 10. OCR Policy

OCR is optional and asynchronous.

OCR failures must not affect capture, enhancement, or export workflows.

OCR output is stored as a searchable text layer attached to pages.

---

## 11. PDF Assembly and Export

PDF export must support:
- Configurable DPI
- Compression settings
- Page ordering
- Embedded OCR text layers

Exported files must be deterministic and reproducible.

Sharing is implemented via time-limited, document-scoped download links.

---

## 12. Deployment and Runtime Behavior

The application runs as a local Flask server.

All state is stored on disk in a predictable directory structure.

Server restarts must not silently destroy document sessions unless explicitly configured to do so.

Failure modes must be explicit and recoverable.

---

## 13. Planning Discipline

Development must follow a gated, step-by-step approach.

Streaming viability must be validated before UI polish or OCR work.

No module may be implemented before its dependencies and interfaces are defined.

The system must always prioritize correctness, clarity, and maintainability over shortcuts.

---

## 14. Definition of Success

The project is successful if a single power user can replace CamScanner with this application for daily document scanning using a desktop browser and a phone on a tripod, without subscriptions, logins, or cloud dependencies.
