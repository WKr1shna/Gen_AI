// LexiRecon Legal Document Reconstructor Client Application

class LexiReconApp {
  constructor() {
    this.currentDoc = null;
    this.comparisonData = null;
    this.zoomLevel = 1.0;
    this.viewMode = "side-by-side"; // "side-by-side", "overlay", "diff"
    this.overlayOpacity = 0.5;
    this.isSyncScrolling = true;

    this.cropState = {
      file: null,
      sourceUrl: null,
      rotation: 0,
      ratio: "free",
      left: 0,
      top: 0,
      width: 0,
      height: 0,
      isDragging: false,
      dragMode: null, // "move", "nw", "n", "ne", "e", "se", "s", "sw", "w"
      startX: 0,
      startY: 0,
      initialBox: null
    };

    this.initElements();
    this.bindEvents();
    this.initCropper();
    
    // Auto-load default legal affidavit sample on startup for instant demonstration
    this.loadSample("affidavit");
  }

  initElements() {
    // Header elements
    this.docTitleEl = document.getElementById("doc-title");
    this.docTypeBadgeEl = document.getElementById("doc-type-badge");
    this.statPagesEl = document.getElementById("stat-pages");
    this.statTextRecEl = document.getElementById("stat-text-rec");
    this.statLayoutSimEl = document.getElementById("stat-layout-sim");
    this.statVisualSimEl = document.getElementById("stat-visual-sim");
    this.statElementsEl = document.getElementById("stat-elements");
    this.statMismatchesEl = document.getElementById("stat-mismatches");

    // Containers
    this.originalContainerEl = document.getElementById("original-container");
    this.reconstructedContainerEl = document.getElementById("reconstructed-container");
    this.appLayoutContainerEl = document.getElementById("app-layout");
    this.loadingOverlayEl = document.getElementById("loading-overlay");
    this.loadingTextEl = document.getElementById("loading-text");

    // Sidebar
    this.fieldListEl = document.getElementById("field-list");
    this.fieldCountEl = document.getElementById("field-count");
    this.fileInputEl = document.getElementById("pdf-file-input");
    this.uploadZoneEl = document.getElementById("upload-zone");

    // Search & Replace
    this.findInputEl = document.getElementById("find-input");
    this.replaceInputEl = document.getElementById("replace-input");
    this.matchCaseCheckEl = document.getElementById("match-case-check");
    this.btnReplaceAllEl = document.getElementById("btn-replace-all");

    // Actions
    this.btnUndoEl = document.getElementById("btn-undo");
    this.btnRedoEl = document.getElementById("btn-redo");
    this.btnExportPdfEl = document.getElementById("btn-export-pdf");
    this.btnExportDocxEl = document.getElementById("btn-export-docx");
    this.btnPrintEl = document.getElementById("btn-print");
    this.btnDeleteDocEl = document.getElementById("btn-delete-doc");

    // View toggles
    this.btnModeSideEl = document.getElementById("btn-mode-side");
    this.btnModeOverlayEl = document.getElementById("btn-mode-overlay");
    this.overlaySliderEl = document.getElementById("overlay-opacity-slider");
    this.overlaySliderBoxEl = document.getElementById("overlay-slider-box");

    // Cropper elements
    this.cropModalOverlay = document.getElementById("crop-modal-overlay");
    this.cropFileNameEl = document.getElementById("crop-file-name");
    this.cropDimensionsLabelEl = document.getElementById("crop-dimensions-label");
    this.cropSourceImgEl = document.getElementById("crop-source-img");
    this.cropWorkspaceEl = document.getElementById("crop-workspace");
    this.cropSelectionBoxEl = document.getElementById("crop-selection-box");
    this.btnCropCancelEl = document.getElementById("btn-crop-cancel");
    this.btnCropSkipEl = document.getElementById("btn-crop-skip");
    this.btnCropApplyEl = document.getElementById("btn-crop-apply");
    this.btnCropRotateEl = document.getElementById("btn-crop-rotate");
    this.btnCropRotateLeftEl = document.getElementById("btn-crop-rotate-left");
    this.btnCropResetEl = document.getElementById("btn-crop-reset");
  }

  bindEvents() {
    // File upload
    this.uploadZoneEl.addEventListener("click", () => this.fileInputEl.click());
    this.fileInputEl.addEventListener("change", (e) => this.handleFileUpload(e));

    // Drag & Drop
    this.uploadZoneEl.addEventListener("dragover", (e) => {
      e.preventDefault();
      this.uploadZoneEl.classList.add("dragover");
    });
    this.uploadZoneEl.addEventListener("dragleave", () => {
      this.uploadZoneEl.classList.remove("dragover");
    });
    this.uploadZoneEl.addEventListener("drop", (e) => {
      e.preventDefault();
      this.uploadZoneEl.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        this.processSelectedFile(e.dataTransfer.files[0]);
      }
    });

    // Sample buttons
    document.querySelectorAll(".sample-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const type = btn.getAttribute("data-sample");
        this.loadSample(type);
      });
    });

    // Search & Replace
    this.btnReplaceAllEl.addEventListener("click", () => this.handleReplaceAll());

    // Undo / Redo
    this.btnUndoEl.addEventListener("click", () => this.undo());
    this.btnRedoEl.addEventListener("click", () => this.redo());

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) {
          this.redo();
        } else {
          this.undo();
        }
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
        e.preventDefault();
        this.redo();
      }
    });

    // Exports
    this.btnExportPdfEl.addEventListener("click", () => this.exportPdf());
    this.btnExportDocxEl.addEventListener("click", () => this.exportDocx());
    this.btnPrintEl.addEventListener("click", () => window.print());
    this.btnDeleteDocEl.addEventListener("click", () => this.deleteDocument());

    // View modes
    this.btnModeSideEl.addEventListener("click", () => this.setViewMode("side-by-side"));
    this.btnModeOverlayEl.addEventListener("click", () => this.setViewMode("overlay"));
    this.overlaySliderEl.addEventListener("input", (e) => {
      this.overlayOpacity = parseFloat(e.target.value);
      this.updateOverlayOpacity();
    });

    // Zoom buttons
    document.getElementById("btn-zoom-in").addEventListener("click", () => this.adjustZoom(0.1));
    document.getElementById("btn-zoom-out").addEventListener("click", () => this.adjustZoom(-0.1));
    document.getElementById("btn-zoom-reset").addEventListener("click", () => this.setZoom(1.0));

    // Page Navigation buttons
    const btnPrev = document.getElementById("btn-prev-page");
    const btnNext = document.getElementById("btn-next-page");
    if (btnPrev) btnPrev.addEventListener("click", () => this.goToPage(this.currentPage - 1));
    if (btnNext) btnNext.addEventListener("click", () => this.goToPage(this.currentPage + 1));

    // Pen Ink Toggle Sync
    const headerPen = document.getElementById("header-ignore-pen");
    const cropPen = document.getElementById("crop-ignore-pen");
    if (headerPen && cropPen) {
      headerPen.addEventListener("change", (e) => { cropPen.checked = e.target.checked; });
      cropPen.addEventListener("change", (e) => { headerPen.checked = e.target.checked; });
    }

    // Synchronized scrolling
    this.setupSyncScroll();
  }

  goToPage(pageNum) {
    if (!this.currentDoc || !this.currentDoc.pages.length) return;
    const total = this.currentDoc.pages.length;
    const targetPage = Math.max(1, Math.min(total, pageNum));
    this.currentPage = targetPage;
    
    const pageNavLabel = document.getElementById("page-nav-label");
    if (pageNavLabel) pageNavLabel.innerText = `Page ${targetPage} / ${total}`;

    const origEl = document.getElementById(`orig-page-${targetPage}`);
    const reconEl = document.getElementById(`page-${targetPage}`);
    if (origEl) origEl.scrollIntoView({ behavior: "smooth", block: "start" });
    if (reconEl) reconEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  showLoading(text = "Processing Legal Document...") {
    this.loadingTextEl.innerText = text;
    this.loadingOverlayEl.classList.add("active");
  }

  hideLoading() {
    this.loadingOverlayEl.classList.remove("active");
  }

  async loadSample(sampleType) {
    this.showLoading(`Loading ${sampleType.toUpperCase()} Legal Sample...`);
    try {
      const res = await fetch(`/api/sample/${sampleType}`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to load sample");
      const doc = await res.json();
      await this.setDocument(doc);
    } catch (err) {
      alert("Error loading sample: " + err.message);
    } finally {
      this.hideLoading();
    }
  }

  async handleFileUpload(e) {
    const file = e.target.files[0];
    if (file) {
      this.processSelectedFile(file);
    }
    this.fileInputEl.value = "";
  }

  processSelectedFile(file) {
    const validExts = [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!validExts.includes(ext)) {
      alert("Please upload a valid PDF or Image file (PNG, JPG, JPEG, WEBP, TIFF, BMP).");
      return;
    }

    // If it's an image, open interactive crop modal first
    const isImage = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"].includes(ext);
    if (isImage) {
      this.openCropModal(file);
    } else {
      // PDF documents upload directly
      this.uploadFile(file);
    }
  }

  /* ==========================================================================
     Interactive Image Crop System
     ========================================================================== */
  initCropper() {
    // Ratio buttons
    document.querySelectorAll(".crop-tool-btn[data-ratio]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".crop-tool-btn[data-ratio]").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.cropState.ratio = btn.getAttribute("data-ratio");
        this.applyAspectRatioConstraint();
      });
    });

    // Rotation controls
    this.btnCropRotateEl.addEventListener("click", () => this.rotateImage(90));
    this.btnCropRotateLeftEl.addEventListener("click", () => this.rotateImage(-90));

    // Reset crop box
    this.btnCropResetEl.addEventListener("click", () => this.resetCropBox());

    // Modal action buttons
    this.btnCropCancelEl.addEventListener("click", () => this.closeCropModal());
    this.btnCropSkipEl.addEventListener("click", () => {
      const fileToUpload = this.cropState.file;
      this.closeCropModal();
      if (fileToUpload) this.uploadFile(fileToUpload);
    });
    this.btnCropApplyEl.addEventListener("click", () => this.applyCropAndUpload());

    // Drag & Resize handling on selection box
    this.cropSelectionBoxEl.addEventListener("pointerdown", (e) => this.onCropPointerDown(e));
    window.addEventListener("pointermove", (e) => this.onCropPointerMove(e));
    window.addEventListener("pointerup", () => this.onCropPointerUp());
    window.addEventListener("pointercancel", () => this.onCropPointerUp());
  }

  openCropModal(file) {
    this.cropState.file = file;
    this.cropState.rotation = 0;
    this.cropState.ratio = "free";
    this.cropFileNameEl.innerText = file.name;

    // Reset active ratio button
    document.querySelectorAll(".crop-tool-btn[data-ratio]").forEach(b => {
      b.classList.toggle("active", b.getAttribute("data-ratio") === "free");
    });

    if (this.cropState.sourceUrl) {
      URL.revokeObjectURL(this.cropState.sourceUrl);
    }
    this.cropState.sourceUrl = URL.createObjectURL(file);
    this.cropSourceImgEl.src = this.cropState.sourceUrl;

    this.cropSourceImgEl.onload = () => {
      this.cropModalOverlay.classList.add("active");
      // Allow image layout to render before calculating dimensions
      requestAnimationFrame(() => {
        this.resetCropBox();
      });
    };
  }

  closeCropModal() {
    this.cropModalOverlay.classList.remove("active");
    if (this.cropState.sourceUrl) {
      URL.revokeObjectURL(this.cropState.sourceUrl);
      this.cropState.sourceUrl = null;
    }
    this.cropState.file = null;
  }

  rotateImage(angle) {
    this.cropState.rotation = (this.cropState.rotation + angle + 360) % 360;
    
    // Create an offscreen canvas to rotate the source image
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.src = this.cropState.sourceUrl;
    img.onload = () => {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      const is90or270 = this.cropState.rotation === 90 || this.cropState.rotation === 270;
      
      canvas.width = is90or270 ? img.naturalHeight : img.naturalWidth;
      canvas.height = is90or270 ? img.naturalWidth : img.naturalHeight;
      
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate((this.cropState.rotation * Math.PI) / 180);
      ctx.drawImage(img, -img.naturalWidth / 2, -img.naturalHeight / 2);
      
      canvas.toBlob((blob) => {
        if (!blob) return;
        if (this.cropState.sourceUrl) {
          URL.revokeObjectURL(this.cropState.sourceUrl);
        }
        this.cropState.sourceUrl = URL.createObjectURL(blob);
        this.cropState.rotation = 0; // Baked into rotated image
        this.cropSourceImgEl.src = this.cropState.sourceUrl;
        this.cropSourceImgEl.onload = () => {
          this.resetCropBox();
        };
      }, this.cropState.file.type || "image/png", 0.95);
    };
  }

  resetCropBox() {
    const imgW = this.cropSourceImgEl.offsetWidth;
    const imgH = this.cropSourceImgEl.offsetHeight;
    if (imgW === 0 || imgH === 0) return;

    // Default crop box with 5% margins
    const marginX = imgW * 0.05;
    const marginY = imgH * 0.05;

    this.cropState.left = marginX;
    this.cropState.top = marginY;
    this.cropState.width = imgW - marginX * 2;
    this.cropState.height = imgH - marginY * 2;

    this.applyAspectRatioConstraint();
    this.updateCropUI();
  }

  applyAspectRatioConstraint() {
    const imgW = this.cropSourceImgEl.offsetWidth;
    const imgH = this.cropSourceImgEl.offsetHeight;
    if (imgW === 0 || imgH === 0) return;

    let targetRatio = null;
    if (this.cropState.ratio === "a4") targetRatio = 1 / 1.4142; // A4 standard ratio (W/H)
    else if (this.cropState.ratio === "1:1") targetRatio = 1.0;
    else if (this.cropState.ratio === "4:3") targetRatio = 4 / 3;

    if (targetRatio !== null) {
      let newW = this.cropState.width;
      let newH = newW / targetRatio;
      if (newH > imgH - this.cropState.top) {
        newH = imgH - this.cropState.top;
        newW = newH * targetRatio;
      }
      if (newW > imgW - this.cropState.left) {
        newW = imgW - this.cropState.left;
        newH = newW / targetRatio;
      }
      this.cropState.width = Math.max(30, newW);
      this.cropState.height = Math.max(30, newH);
    }
    this.updateCropUI();
  }

  onCropPointerDown(e) {
    e.preventDefault();
    const handle = e.target.getAttribute("data-handle");
    this.cropState.isDragging = true;
    this.cropState.dragMode = handle || "move";
    this.cropState.startX = e.clientX;
    this.cropState.startY = e.clientY;
    this.cropState.initialBox = {
      left: this.cropState.left,
      top: this.cropState.top,
      width: this.cropState.width,
      height: this.cropState.height
    };
    this.cropSelectionBoxEl.setPointerCapture(e.pointerId);
  }

  onCropPointerMove(e) {
    if (!this.cropState.isDragging) return;
    const dx = e.clientX - this.cropState.startX;
    const dy = e.clientY - this.cropState.startY;
    const imgW = this.cropSourceImgEl.offsetWidth;
    const imgH = this.cropSourceImgEl.offsetHeight;
    const init = this.cropState.initialBox;

    let newL = init.left;
    let newT = init.top;
    let newW = init.width;
    let newH = init.height;

    const mode = this.cropState.dragMode;

    if (mode === "move") {
      newL = Math.max(0, Math.min(imgW - newW, init.left + dx));
      newT = Math.max(0, Math.min(imgH - newH, init.top + dy));
    } else {
      // Handle resizing
      if (mode.includes("e")) {
        newW = Math.max(30, Math.min(imgW - init.left, init.width + dx));
      }
      if (mode.includes("s")) {
        newH = Math.max(30, Math.min(imgH - init.top, init.height + dy));
      }
      if (mode.includes("w")) {
        const potentialL = init.left + dx;
        if (potentialL >= 0 && init.width - dx >= 30) {
          newL = potentialL;
          newW = init.width - dx;
        }
      }
      if (mode.includes("n")) {
        const potentialT = init.top + dy;
        if (potentialT >= 0 && init.height - dy >= 30) {
          newT = potentialT;
          newH = init.height - dy;
        }
      }

      // Maintain aspect ratio if fixed
      let targetRatio = null;
      if (this.cropState.ratio === "a4") targetRatio = 1 / 1.4142;
      else if (this.cropState.ratio === "1:1") targetRatio = 1.0;
      else if (this.cropState.ratio === "4:3") targetRatio = 4 / 3;

      if (targetRatio !== null) {
        if (mode === "e" || mode === "w") {
          newH = newW / targetRatio;
        } else {
          newW = newH * targetRatio;
        }
        if (newL + newW > imgW) newW = imgW - newL;
        if (newT + newH > imgH) newH = imgH - newT;
      }
    }

    this.cropState.left = newL;
    this.cropState.top = newT;
    this.cropState.width = newW;
    this.cropState.height = newH;

    this.updateCropUI();
  }

  onCropPointerUp() {
    this.cropState.isDragging = false;
    this.cropState.dragMode = null;
  }

  updateCropUI() {
    this.cropSelectionBoxEl.style.left = `${this.cropState.left}px`;
    this.cropSelectionBoxEl.style.top = `${this.cropState.top}px`;
    this.cropSelectionBoxEl.style.width = `${this.cropState.width}px`;
    this.cropSelectionBoxEl.style.height = `${this.cropState.height}px`;

    // Calculate natural image pixel dimensions for the badge
    const scaleX = this.cropSourceImgEl.naturalWidth / (this.cropSourceImgEl.offsetWidth || 1);
    const scaleY = this.cropSourceImgEl.naturalHeight / (this.cropSourceImgEl.offsetHeight || 1);

    const naturalW = Math.round(this.cropState.width * scaleX);
    const naturalH = Math.round(this.cropState.height * scaleY);
    this.cropDimensionsLabelEl.innerText = `${naturalW} × ${naturalH} px`;
  }

  async applyCropAndUpload() {
    const img = this.cropSourceImgEl;
    if (!img.naturalWidth || !img.naturalHeight) {
      alert("Image is not loaded yet.");
      return;
    }

    const scaleX = img.naturalWidth / img.offsetWidth;
    const scaleY = img.naturalHeight / img.offsetHeight;

    const cropX = Math.round(this.cropState.left * scaleX);
    const cropY = Math.round(this.cropState.top * scaleY);
    const cropW = Math.round(this.cropState.width * scaleX);
    const cropH = Math.round(this.cropState.height * scaleY);

    if (cropW <= 0 || cropH <= 0) {
      alert("Please select a valid crop area.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = cropW;
    canvas.height = cropH;
    const ctx = canvas.getContext("2d");

    // Draw high-resolution cropped slice
    ctx.drawImage(img, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH);

    const originalFile = this.cropState.file;

    canvas.toBlob((blob) => {
      if (!blob) {
        alert("Failed to create cropped image blob.");
        return;
      }
      const croppedFileName = originalFile.name.replace(/\.[^/.]+$/, "") + "_cropped.png";
      const croppedFile = new File([blob], croppedFileName, { type: "image/png" });

      this.closeCropModal();
      this.uploadFile(croppedFile);
    }, "image/png", 0.98);
  }

  async uploadFile(file) {
    const validExts = [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!validExts.includes(ext)) {
      alert("Please upload a valid PDF or Image file (PNG, JPG, JPEG, WEBP, TIFF, BMP).");
      return;
    }

    const headerIgnore = document.getElementById("header-ignore-pen");
    const cropIgnore = document.getElementById("crop-ignore-pen");
    const shouldIgnorePen = (cropIgnore ? cropIgnore.checked : (headerIgnore ? headerIgnore.checked : true));

    this.showLoading(shouldIgnorePen ? `Filtering Pen Ink & Reconstructing Clean Template for ${file.name}...` : `Analyzing and Reconstructing ${file.name}...`);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("ignore_pen_ink", shouldIgnorePen ? "true" : "false");

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Document processing failed.");
      const doc = await res.json();
      await this.setDocument(doc);
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      this.hideLoading();
    }
  }

  async setDocument(doc) {
    this.currentDoc = doc;
    this.updateHeaderStats();
    this.renderOriginalPages();
    await this.renderReconstructedPages();
    this.renderSmartFields();
    this.fetchComparisonMetrics();
  }

  async fetchComparisonMetrics() {
    if (!this.currentDoc) return;
    try {
      const res = await fetch(`/api/document/${this.currentDoc.id}/compare`);
      if (res.ok) {
        this.comparisonData = await res.json();
        this.statTextRecEl.innerText = `${this.comparisonData.text_recovery_pct}%`;
        this.statLayoutSimEl.innerText = `${this.comparisonData.layout_similarity_pct}%`;
        this.statVisualSimEl.innerText = `${this.comparisonData.visual_similarity_pct}%`;
        if (this.statElementsEl && this.comparisonData.elements_compared !== undefined) {
          this.statElementsEl.innerText = this.comparisonData.elements_compared;
        }
        if (this.statMismatchesEl && this.comparisonData.major_mismatches !== undefined) {
          this.statMismatchesEl.innerText = this.comparisonData.major_mismatches;
        }
      }
    } catch (e) {
      console.error("Comparison fetch failed", e);
    }
  }

  updateHeaderStats() {
    if (!this.currentDoc) return;
    this.docTitleEl.innerText = this.currentDoc.filename;
    
    // PDF type badge
    const docType = this.currentDoc.doc_type;
    this.docTypeBadgeEl.className = `badge-tag badge-${docType}`;
    this.docTypeBadgeEl.innerText = 
      docType === "digital" ? "Digitally Generated (Vector)" :
      docType === "scanned" ? "Scanned (OCR Reconstructed)" : "Mixed (Text + Images)";

    const stats = this.currentDoc.stats;
    this.currentPage = 1;
    const pageNavLabel = document.getElementById("page-nav-label");
    if (pageNavLabel) pageNavLabel.innerText = `Page 1 / ${stats.page_count}`;

    this.statPagesEl.innerText = `${stats.page_count} → ${stats.page_count}`;
    this.statTextRecEl.innerText = `${stats.text_recovery_pct}%`;
    this.statLayoutSimEl.innerText = `${stats.layout_similarity_pct}%`;
    this.statVisualSimEl.innerText = `${stats.visual_similarity_pct}%`;
    if (this.statElementsEl && stats.elements_compared !== undefined) {
      this.statElementsEl.innerText = stats.elements_compared;
    }
    if (this.statMismatchesEl && stats.major_mismatches !== undefined) {
      this.statMismatchesEl.innerText = stats.major_mismatches;
    }
  }

  renderOriginalPages() {
    this.originalContainerEl.innerHTML = "";
    if (!this.currentDoc) return;

    this.currentDoc.pages.forEach((page) => {
      const wrapper = document.createElement("div");
      wrapper.className = "page-preview-wrapper";
      wrapper.id = `orig-page-${page.page_number}`;
      wrapper.style.width = `${page.width}pt`;
      wrapper.style.height = `${page.height}pt`;
      wrapper.setAttribute("data-base-height", page.height);

      const img = document.createElement("img");
      img.className = "original-page-img";
      img.loading = "lazy";
      img.decoding = "async";
      img.src = page.original_image_base64 
        ? `data:image/png;base64,${page.original_image_base64}` 
        : `/api/document/${this.currentDoc.id}/page/${page.page_number}/image`;
      img.style.width = "100%";
      img.style.height = "100%";
      wrapper.appendChild(img);
      this.originalContainerEl.appendChild(wrapper);
    });
  }

  async renderReconstructedPages() {
    this.reconstructedContainerEl.innerHTML = "";
    if (!this.currentDoc) return;

    try {
      const res = await fetch(`/api/document/${this.currentDoc.id}/html`);
      const data = await res.json();
      this.reconstructedContainerEl.innerHTML = data.html;

      this.attachSpanEditListeners();
      this.applyZoom();
      if (this.viewMode === "overlay") {
        this.attachOverlayBackgrounds();
      }
    } catch (err) {
      console.error("Failed to load editable HTML", err);
    }
  }

  attachSpanEditListeners() {
    const spans = this.reconstructedContainerEl.querySelectorAll(".text-span");
    spans.forEach((span) => {
      const spanId = span.getAttribute("data-span-id");
      const pageNum = parseInt(span.getAttribute("data-page"), 10);

      // Save on blur
      span.addEventListener("blur", () => {
        const newText = span.innerText;
        this.updateSpanText(spanId, pageNum, newText);
      });

      // Prevent Enter key from breaking coordinates
      span.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          span.blur();
        }
      });
    });
  }

  async updateSpanText(spanId, pageNumber, newText) {
    if (!this.currentDoc) return;
    try {
      const res = await fetch(`/api/document/${this.currentDoc.id}/update-span`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          span_id: spanId,
          new_text: newText,
          page_number: pageNumber,
        }),
      });
      if (res.ok) {
        this.currentDoc = await res.json();
        this.renderSmartFields();
      }
    } catch (err) {
      console.error("Failed to update span", err);
    }
  }

  renderSmartFields() {
    this.fieldListEl.innerHTML = "";
    if (!this.currentDoc || !this.currentDoc.global_fields) return;

    const fields = this.currentDoc.global_fields;
    this.fieldCountEl.innerText = fields.length;

    if (fields.length === 0) {
      this.fieldListEl.innerHTML = `<div style="font-size:0.75rem; color:var(--text-muted); padding:8px;">No template variables detected.</div>`;
      return;
    }

    fields.forEach((field) => {
      const item = document.createElement("div");
      item.className = "field-item";
      item.id = `field-item-${field.id}`;

      const displayVal = field.current_text || field.original_text || "";

      item.innerHTML = `
        <div class="field-header">
          <span class="field-label">${field.label}</span>
          <span class="field-occurrences">${field.occurrence_count}x (${Math.round(field.confidence * 100)}%)</span>
        </div>
        <input type="text" class="field-input" value="${displayVal.replace(/"/g, '&quot;')}" />
      `;

      const input = item.querySelector(".field-input");
      input.addEventListener("input", (e) => {
        this.updateFieldLive(field.id, e.target.value);
      });

      // Highlight corresponding spans on focus
      input.addEventListener("focus", () => {
        item.classList.add("active");
        this.highlightFieldSpans(field.id, true);
      });
      input.addEventListener("blur", () => {
        item.classList.remove("active");
        this.highlightFieldSpans(field.id, false);
      });

      this.fieldListEl.appendChild(item);
    });
  }

  highlightFieldSpans(fieldId, isHighlight) {
    const spans = this.reconstructedContainerEl.querySelectorAll(`[data-field-id="${fieldId}"]`);
    spans.forEach((s) => {
      if (isHighlight) {
        s.style.boxShadow = "0 0 0 2px #f59e0b, 0 0 8px rgba(245, 158, 11, 0.6)";
        s.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        s.style.boxShadow = "none";
      }
    });
  }

  async updateFieldLive(fieldId, newValue) {
    if (!this.currentDoc) return;

    // Instantly update DOM nodes without shifting layout
    const spans = this.reconstructedContainerEl.querySelectorAll(`[data-field-id="${fieldId}"]`);
    spans.forEach((span) => {
      span.innerText = newValue;
    });

    try {
      await fetch(`/api/document/${this.currentDoc.id}/update-field`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          field_id: fieldId,
          new_value: newValue,
          apply_to_all_occurrences: true,
        }),
      });
    } catch (err) {
      console.error("Field update failed", err);
    }
  }

  async handleReplaceAll() {
    if (!this.currentDoc) return;
    const findText = this.findInputEl.value;
    const replaceText = this.replaceInputEl.value;
    const matchCase = this.matchCaseCheckEl.checked;

    if (!findText) {
      alert("Please enter text to find.");
      return;
    }

    try {
      const res = await fetch(`/api/document/${this.currentDoc.id}/replace-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          find_text: findText,
          replace_text: replaceText,
          match_case: matchCase,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        alert(`Replaced ${data.replaced_count} occurrence(s).`);
        this.currentDoc = data.document;
        await this.renderReconstructedPages();
        this.renderSmartFields();
      }
    } catch (err) {
      alert("Replace failed: " + err.message);
    }
  }

  async undo() {
    if (!this.currentDoc) return;
    try {
      const res = await fetch(`/api/document/${this.currentDoc.id}/undo`, { method: "POST" });
      if (res.ok) {
        this.currentDoc = await res.json();
        await this.renderReconstructedPages();
        this.renderSmartFields();
      }
    } catch (err) {
      console.error("Undo failed", err);
    }
  }

  async redo() {
    if (!this.currentDoc) return;
    try {
      const res = await fetch(`/api/document/${this.currentDoc.id}/redo`, { method: "POST" });
      if (res.ok) {
        this.currentDoc = await res.json();
        await this.renderReconstructedPages();
        this.renderSmartFields();
      }
    } catch (err) {
      console.error("Redo failed", err);
    }
  }

  setViewMode(mode) {
    this.viewMode = mode;
    if (mode === "overlay") {
      this.appLayoutContainerEl.classList.add("mode-overlay");
      document.getElementById("original-panel-col").style.display = "none";
      this.overlaySliderBoxEl.style.display = "flex";
      this.btnModeOverlayEl.classList.add("btn-gold");
      this.btnModeSideEl.classList.remove("btn-gold");
      this.attachOverlayBackgrounds();
    } else {
      this.appLayoutContainerEl.classList.remove("mode-overlay");
      document.getElementById("original-panel-col").style.display = "flex";
      this.overlaySliderBoxEl.style.display = "none";
      this.btnModeSideEl.classList.add("btn-gold");
      this.btnModeOverlayEl.classList.remove("btn-gold");
      this.removeOverlayBackgrounds();
    }
  }

  attachOverlayBackgrounds() {
    if (!this.currentDoc) return;
    this.currentDoc.pages.forEach((page) => {
      const pageEl = document.getElementById(`page-${page.page_number}`);
      if (pageEl && page.original_image_base64) {
        pageEl.style.backgroundImage = `url('data:image/png;base64,{page.original_image_base64}')`.replace("{page.original_image_base64}", page.original_image_base64);
        pageEl.style.backgroundSize = "100% 100%";
        pageEl.style.backgroundRepeat = "no-repeat";
      }
    });
    this.updateOverlayOpacity();
  }

  removeOverlayBackgrounds() {
    if (!this.currentDoc) return;
    this.currentDoc.pages.forEach((page) => {
      const pageEl = document.getElementById(`page-${page.page_number}`);
      if (pageEl) {
        pageEl.style.backgroundImage = "none";
      }
    });
    const spans = this.reconstructedContainerEl.querySelectorAll(".text-span, .page-drawings, .doc-image");
    spans.forEach((el) => {
      el.style.opacity = 1.0;
    });
  }

  updateOverlayOpacity() {
    if (this.viewMode !== "overlay") return;
    const spans = this.reconstructedContainerEl.querySelectorAll(".text-span, .page-drawings, .doc-image");
    spans.forEach((el) => {
      el.style.opacity = this.overlayOpacity;
    });
  }

  adjustZoom(delta) {
    this.setZoom(Math.max(0.4, Math.min(2.0, this.zoomLevel + delta)));
  }

  setZoom(val) {
    this.zoomLevel = Math.round(val * 10) / 10;
    document.getElementById("zoom-level-label").innerText = `${Math.round(this.zoomLevel * 100)}%`;
    this.applyZoom();
  }

  applyZoom() {
    const scale = this.zoomLevel;
    const pages = document.querySelectorAll(".doc-page, .page-preview-wrapper");
    pages.forEach((p) => {
      p.style.transform = `scale(${scale})`;
      p.style.transformOrigin = "top center";
      const baseHeight = parseFloat(p.getAttribute("data-base-height") || 842);
      if (scale > 1.0) {
        p.style.marginBottom = `${30 + baseHeight * (scale - 1)}px`;
      } else {
        p.style.marginBottom = "30px";
      }
    });
  }

  setupSyncScroll() {
    let isOriginalScrolling = false;
    let isReconstructedScrolling = false;

    this.originalContainerEl.addEventListener("scroll", () => {
      if (!isOriginalScrolling && this.isSyncScrolling) {
        isReconstructedScrolling = true;
        this.reconstructedContainerEl.scrollTop = this.originalContainerEl.scrollTop;
        this.reconstructedContainerEl.scrollLeft = this.originalContainerEl.scrollLeft;
        setTimeout(() => (isReconstructedScrolling = false), 50);
      }
    }, { passive: true });

    this.reconstructedContainerEl.addEventListener("scroll", () => {
      if (!isReconstructedScrolling && this.isSyncScrolling) {
        isOriginalScrolling = true;
        this.originalContainerEl.scrollTop = this.reconstructedContainerEl.scrollTop;
        this.originalContainerEl.scrollLeft = this.reconstructedContainerEl.scrollLeft;
        setTimeout(() => (isOriginalScrolling = false), 50);
      }
    }, { passive: true });
  }

  exportPdf() {
    if (!this.currentDoc) return;
    window.location.href = `/api/document/${this.currentDoc.id}/export/pdf`;
  }

  exportDocx() {
    if (!this.currentDoc) return;
    window.location.href = `/api/document/${this.currentDoc.id}/export/docx`;
  }

  async deleteDocument() {
    if (!this.currentDoc) return;
    if (confirm("Are you sure you want to permanently delete this document and wipe it from local memory?")) {
      await fetch(`/api/document/${this.currentDoc.id}`, { method: "DELETE" });
      this.currentDoc = null;
      this.originalContainerEl.innerHTML = "";
      this.reconstructedContainerEl.innerHTML = "";
      this.fieldListEl.innerHTML = "";
      this.docTitleEl.innerText = "No document loaded";
      this.docTypeBadgeEl.innerText = "NONE";
      alert("Document securely purged from local memory.");
    }
  }
}

// Initialize on DOM load
window.addEventListener("DOMContentLoaded", () => {
  window.app = new LexiReconApp();
});
