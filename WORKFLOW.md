# Lecture-note production workflow

This independent edition uses the NPTEL Mathematical Foundations for Machine
Learning recordings by Ashok Rao and Arulalan Rajan as its chronological spine.
All 70 numbered lectures and the introduction are assigned once across 26 topic
chapters. The original playlist is reverse ordered; the source manifest retains
its positions while the reader follows ascending lecture numbers.

The production skills are `transcript-grounded-textbook`, `rigorous-explainer`,
and `science-editor`. The user authorized autonomous completion, a public GitHub
repository, and GitHub Pages publication. Working artifacts remain inside the
project directory; raw sources and private editorial records are excluded from
Git and from the public package.

1. Enumerate the exact playlist and verify course identity against the official
   syllabus. Preserve recording identifiers, titles, source positions, actual
   durations, and chapter assignments.
2. Acquire the best available English caption tracks. Retain their labels,
   language, hashes, segment timing, and provenance limits. A publisher label
   such as “NPTEL Verified” does not establish human authorship or perfect
   mathematical transcription. Lecture 55 supplies no English YouTube captions;
   its full audio is transcribed locally with Whisper `small.en` and recorded
   separately as machine recognition.
3. Calibrate the prose against complete Stanford CS229 chapters and the existing
   NPTEL reader. Develop a representative pilot through source reading,
   mathematical exposition, six worked problems, scientific review, executable
   checks, and offline desktop/mobile rendering.
4. Read each assigned transcript sequentially. Map its substantive topic changes,
   examples, distinctions, and timing. Preserve consolidation and summary
   recordings rather than omitting them because they repeat earlier material.
5. Develop original textbook prose with local definitions, domains, assumptions,
   consequential derivation steps, recurring cases, numerical checks, limits,
   and six fully worked problems per chapter. Inspect precise sections of
   primary-author mathematical references before citing them. Distinguish
   lecture material, reference-supported extensions, and teaching constructions.
6. Send draft manuscripts to scientific editing. Substantial repairs can require
   a full rewrite. A repairing author cannot independently accept that rewrite;
   final scientific acceptance requires a separate reviewer and an exact body
   digest. Keep findings, repairs, and review rounds distinct from mechanical
   validation. Caption discrepancies are not attributed to an instructor without
   audiovisual confirmation.
7. Check book-wide dependencies and notation, especially data-matrix orientation,
   scalar field, basis versus spanning set, eigenvalue multiplicities, covariance
   centering and normalization, independence versus correlation, finite-moment
   assumptions, derivative shapes, constrained stationarity, stable step sizes,
   and existence of logistic-regression minimizers.
8. Wrap stable authored bodies with the shared reader, preserving their exact
   SHA256 digests. Reuse the NPTEL CSS, JavaScript, local MathJax, and its license.
   Validate every Python listing by actual execution and displayed-output
   comparison. Check every page offline at desktop/mobile widths, including
   mathematical rendering, navigation, contents, search, theme, text size,
   solutions, and print behavior.
9. Audit the public file inventory for private artifacts and credentials. Rebuild
   and verify an isolated Git export without source materials. Keep local Git
   checkpoints, publish the authorized repository and Pages edition, and verify
   served files and live reader behavior. A successful push alone does not
   establish a successful publication.

The numerical laboratory uses constructed examples to connect identifiability,
principal components, probability tails, matrix gradients, and stable quadratic
updates. Its assertions check those implementations; they do not establish
real-world predictive quality or formal verification of every mathematical claim.

Source acquisition, scientific acceptance, code execution, browser behavior,
clean-export reproducibility, and live publication have separate evidence records.
Complete transcript acquisition and endpoint timing do not prove every spoken
word was captured. Comprehensive audiovisual review and human accessibility
certification are not claimed. Chapter sidecars and curated verification records
state the actual checks and their boundaries.
