# Literature Review

Phase 1 deliverable. Status: draft. A team member must spot-check at least 10 citations by opening each link in a browser (Phase 1 test).

## How sources were checked

Every source below was found by web search and then confirmed by opening a page with its title, authors and year. Nothing here is taken from memory alone.

Each verified entry has one of two marks:

| Mark | Meaning |
|---|---|
| **yes (P)** | We opened a primary page: the publisher, the official standards or government page, arXiv, ACL Anthology, USENIX, IETF RFC Editor, NIST, the IACR ePrint archive, or the official repository. |
| **yes (R)** | The publisher page blocked automated access. We confirmed the title, authors, venue and year from the DOI registry record (Crossref), and read the abstract from an abstract index (OpenAlex, Semantic Scholar, PubMed) or an author-hosted PDF. These should be opened in a normal browser during the team spot-check. |

Summaries are in our own words and describe only what the abstract or page says. Where the abstract was not seen, the summary is marked `TODO: verify`.

**Counts:** 79 verified sources (45 marked P, 34 marked R). 13 more are in the "Unverified, needs checking" list at the end.

---

## 1. Secure document management and digital evidence management systems

**1.1 Turner 2005, Digital Evidence Bags**
- Citation: Philip Turner. "Unification of digital evidence from disparate sources (Digital Evidence Bags)." *Digital Investigation*, 2(3), 223-228, 2005.
- Year: 2005 | Venue: Digital Investigation (Elsevier) | Link: https://doi.org/10.1016/j.diin.2005.07.001 | Verified: yes (R). Abstract not seen.
- Summary: Proposes a "Digital Evidence Bag", one container format for evidence from different kinds of devices. It is described elsewhere as carrying an audit trail and integrity checks. TODO: verify against the full text.
- How it relates to Pramaan: An early model for keeping evidence together with its metadata and handling history, as our document record does.
- Its limit for our problem: Works on whole captured data with exact integrity checks. It does not reason about document content or harmless rescans.

**1.2 Prayudi, Ashari and Priyambodo 2014, Digital Evidence Cabinets**
- Citation: Yudi Prayudi, Ahmad Ashari, Tri K. Priyambodo. "Digital Evidence Cabinets: A Proposed Framework for Handling Digital Chain of Custody." *International Journal of Computer Applications*, 107(9), 30-36, 2014.
- Year: 2014 | Venue: IJCA | Link: https://doi.org/10.5120/18781-0106 | Verified: yes (R)
- Summary: Says that chain of custody for digital evidence is harder than for physical evidence and is still open: parties interact, metadata must be recorded, and access must be controlled. Proposes "Digital Evidence Cabinets" that combine an evidence management framework, evidence bags and access control.
- How it relates to Pramaan: Combines evidence storage, metadata and access control in one place, as our document store and access control do.
- Its limit for our problem: A conceptual framework. No content-level fingerprinting and nothing for multilingual documents.

**1.3 NIST IR 8387 (2022), Digital Evidence Preservation**
- Citation: Barbara Guttman, Douglas R. White, Shannan Williams, Tracy Walraven. "Digital Evidence Preservation: Considerations for Evidence Handlers." NIST Interagency Report 8387, 2022.
- Year: 2022 | Venue: NIST | Link: https://doi.org/10.6028/NIST.IR.8387 | Verified: yes (P), opened nist.gov page. TODO: verify the author list on the PDF cover (one snippet lists three authors).
- Summary: Explains how preserving digital evidence differs from preserving other evidence. Covers storage media, digital objects and evidence created by law enforcement itself, and is written for evidence handlers.
- How it relates to Pramaan: Practical preservation guidance for the same users we target.
- Its limit for our problem: Guidance, not a system or method. Does not deal with scans or photos of paper documents.

**1.4 Garfinkel 2010, Digital forensics research: the next 10 years**
- Citation: Simson L. Garfinkel. "Digital forensics research: The next 10 years." *Digital Investigation*, 7, S64-S73, 2010.
- Year: 2010 | Venue: Digital Investigation (DFRWS 2010) | Link: https://doi.org/10.1016/j.diin.2010.05.009 | Verified: yes (R)
- Summary: Argues that digital forensics research lacks a shared strategy, so tools may fall behind and results may lose trust. Calls for standard, modular ways to represent and process forensic data.
- How it relates to Pramaan: Supports storing structured, field-level records instead of opaque files.
- Its limit for our problem: A position paper with no integrity method for documents.

## 2. Chain of custody for digital evidence

**2.1 Cosic and Baca 2010, chain of custody framework**
- Citation: Jasmin Cosic, Miroslav Baca. "A framework to (Im)Prove 'Chain of Custody' in Digital Investigation Process." Central European Conference on Information and Intelligent Systems (CECIIS), 2010.
- Year: 2010 | Venue: CECIIS 2010 | Link: https://archive.ceciis.foi.hr/index.php/ceciis/2010/paper/view/363.html | Verified: yes (P)
- Summary: Argues that chain of custody is central to digital forensics and that custody can break at many points in the evidence life cycle. Proposes a framework to improve custody across collection, transport, analysis, preservation and handling.
- How it relates to Pramaan: A process model for custody records, which we implement as logged custody events.
- Its limit for our problem: A framework proposal. No content-aware integrity and no verification of scanned copies.

**2.2 Lone and Mir 2019, Forensic-chain**
- Citation: Auqib Hamid Lone, Roohie Naaz Mir. "Forensic-chain: Blockchain based digital forensics chain of custody with PoC in Hyperledger Composer." *Digital Investigation*, 28, 44-55, 2019.
- Year: 2019 | Venue: Digital Investigation | Link: https://doi.org/10.1016/j.diin.2019.01.002 | Verified: yes (R)
- Summary: Argues that digital evidence is fragile and crosses jurisdictions, so integrity, authenticity and auditability must hold at every custody stage. Builds a blockchain-based chain of custody as a proof of concept in Hyperledger Composer and evaluates it.
- How it relates to Pramaan: Close prior work on tamper-evident custody records. We aim for a similar goal with a Merkle transparency log instead of a blockchain.
- Its limit for our problem: Protects custody records of evidence items. Does not compare document content across copies.

**2.3 Bonomi, Casini and Ciccotelli 2020, B-CoC**
- Citation: Silvia Bonomi, Marco Casini, Claudio Ciccotelli. "B-CoC: A Blockchain-Based Chain of Custody for Evidences Management in Digital Forensics." Tokenomics 2019, OASIcs vol. 71, 12:1-12:15, 2020.
- Year: 2020 | Venue: OASIcs (Schloss Dagstuhl) | Link: https://doi.org/10.4230/OASIcs.Tokenomics.2019.12 | Verified: yes (P)
- Summary: Notes that custody of digital evidence is often still handled on paper. Proposes moving it onto a blockchain for auditable integrity and traceability, with an Ethereum prototype.
- How it relates to Pramaan: Motivates a digital, auditable custody log.
- Its limit for our problem: Tracks who held evidence. Cannot tell a harmless reprint from a content edit.

**2.4 Alruwaili 2021, CustodyBlock**
- Citation: Fahad F. Alruwaili. "CustodyBlock: A Distributed Chain of Custody Evidence Framework." *Information*, 12(2), 88, 2021.
- Year: 2021 | Venue: Information (MDPI) | Link: https://doi.org/10.3390/info12020088 | Verified: yes (R)
- Summary: A chain of custody model on a private blockchain with smart contracts. Covers control, transfer, analysis and preservation of evidence, with smart contracts automating the steps.
- How it relates to Pramaan: Automates custody transfers, similar to our custody events and approval rules.
- Its limit for our problem: Focuses on custody workflow. No content-aware document comparison.

**2.5 Khan et al. 2021, MF-Ledger**
- Citation: Abdullah Ayub Khan, Mueen Uddin, Aftab Ahmed Shaikh, Asif Ali Laghari, Adil E. Rajput. "MF-Ledger: Blockchain Hyperledger Sawtooth-Enabled Novel and Secure Multimedia Chain of Custody Forensic Investigation Architecture." *IEEE Access*, 9, 103637-103650, 2021.
- Year: 2021 | Venue: IEEE Access | Link: https://doi.org/10.1109/access.2021.3099037 | Verified: yes (R)
- Summary: A permissioned blockchain design on Hyperledger Sawtooth for multimedia forensic investigations. Stakeholders agree on activities before they are recorded, and smart contracts manage their interactions.
- How it relates to Pramaan: Combines protected storage with a shared custody ledger, close to our encrypted storage plus transparency log.
- Its limit for our problem: Targets multimedia evidence custody. No field-level or text-level comparison.

## 3. Cryptographic hashing and digital signatures for evidence integrity

**3.1 FIPS 180-4, Secure Hash Standard**
- Citation: National Institute of Standards and Technology. "Secure Hash Standard (SHS)." FIPS PUB 180-4, 2015.
- Year: 2015 | Venue: NIST FIPS | Link: https://doi.org/10.6028/NIST.FIPS.180-4 | Verified: yes (P)
- Summary: Defines the SHA family of hash algorithms. Comparing a stored digest with a new one shows whether a message has changed.
- How it relates to Pramaan: SHA-256 is our exact-file check (the Identical verdict) and the base of our HMACs and Merkle tree.
- Its limit for our problem: Any changed bit gives a new digest, so a harmless rescan looks the same as a real edit.

**3.2 RFC 2104, HMAC**
- Citation: H. Krawczyk, M. Bellare, R. Canetti. "HMAC: Keyed-Hashing for Message Authentication." RFC 2104, IETF, 1997.
- Year: 1997 | Venue: IETF RFC | Link: https://www.rfc-editor.org/info/rfc2104 | Verified: yes (P)
- Summary: Describes HMAC, which combines a hash function with a secret key to authenticate messages. Its strength depends on the hash used.
- How it relates to Pramaan: Our per-field fingerprints (F) are HMAC-SHA-256 values. The key stops guessing attacks on short values like dates.
- Its limit for our problem: Needs exact input. It only survives rescans if OCR and normalization produce the same value first.

**3.3 NIST SP 800-38D, GCM**
- Citation: Morris Dworkin. "Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC." NIST SP 800-38D, 2007.
- Year: 2007 | Venue: NIST SP | Link: https://doi.org/10.6028/NIST.SP.800-38D | Verified: yes (P). The page notes NIST plans to revise it.
- Summary: Specifies GCM, an authenticated encryption mode, and GMAC, its authentication-only form.
- How it relates to Pramaan: We encrypt stored originals with AES-256-GCM.
- Its limit for our problem: Protects stored bytes only. Says nothing about comparing copies.

**3.4 RFC 8032, EdDSA**
- Citation: S. Josefsson, I. Liusvaara. "Edwards-Curve Digital Signature Algorithm (EdDSA)." RFC 8032, IRTF, 2017.
- Year: 2017 | Venue: IETF RFC | Link: https://www.rfc-editor.org/info/rfc8032 | Verified: yes (P)
- Summary: Describes the EdDSA signature scheme with parameters for edwards25519 and edwards448, with test vectors.
- How it relates to Pramaan: The specification for our Ed25519 seals on intake and fingerprint records.
- Its limit for our problem: A signature covers exact bytes, so a signed scan does not verify against a rescan.

**3.5 Bernstein et al. 2012, Ed25519**
- Citation: Daniel J. Bernstein, Niels Duif, Tanja Lange, Peter Schwabe, Bo-Yin Yang. "High-speed high-security signatures." *Journal of Cryptographic Engineering*, 2(2), 77-89, 2012.
- Year: 2012 | Venue: J. Cryptographic Engineering (Springer) | Link: https://doi.org/10.1007/s13389-012-0027-1 | Verified: yes (P), IACR ePrint 2011/368 plus Crossref.
- Summary: Presents the Ed25519 signature system, with small keys and signatures, fast signing and verification, and defences against software side-channel attacks.
- How it relates to Pramaan: The design basis for our signature scheme.
- Its limit for our problem: Same exact-bytes limit as RFC 8032.

**3.6 RFC 3161, Time-Stamp Protocol**
- Citation: C. Adams, P. Cain, D. Pinkas, R. Zuccherato. "Internet X.509 Public Key Infrastructure Time-Stamp Protocol (TSP)." RFC 3161, IETF, 2001.
- Year: 2001 | Venue: IETF RFC | Link: https://www.rfc-editor.org/info/rfc3161 | Verified: yes (P)
- Summary: Defines how to request and receive a time-stamp from a Time Stamping Authority. A time-stamp shows that data existed before a given time.
- How it relates to Pramaan: We get an RFC 3161 token at intake to prove when a document was sealed. The backdating checks use it.
- Its limit for our problem: Stamps a hash of exact bytes. Says nothing about content equivalence.

**3.7 Haber and Stornetta 1991, time-stamping**
- Citation: Stuart Haber, W. Scott Stornetta. "How to time-stamp a digital document." *Journal of Cryptology*, 3(2), 99-111, 1991.
- Year: 1991 | Venue: Journal of Cryptology | Link: https://doi.org/10.1007/bf00196791 | Verified: yes (R)
- Summary: Proposes ways to time-stamp digital data so that back-dating or forward-dating is not feasible, even if the time-stamping service is not trusted. The service does not need to keep the documents.
- How it relates to Pramaan: The foundation of linked time-stamping and hash-chained logs, behind both RFC 3161 and transparency logs.
- Its limit for our problem: Deliberately exact to the bit, which is why rescans look like tampering.

## 4. Fuzzy and similarity hashing

**4.1 Kornblum 2006, ssdeep (context triggered piecewise hashing)**
- Citation: Jesse Kornblum. "Identifying almost identical files using context triggered piecewise hashing." *Digital Investigation*, 3, 91-97, 2006.
- Year: 2006 | Venue: Digital Investigation | Link: https://doi.org/10.1016/j.diin.2006.06.015 | Verified: yes (R)
- Summary: Builds a file signature from many small hashes whose boundaries are set by the content. This lets it match edited versions of a known file after bytes are inserted, changed or removed.
- How it relates to Pramaan: The ssdeep baseline in our benchmark.
- Its limit for our problem: Works on raw bytes. A rescan or photo of the same page has completely different bytes.

**4.2 Roussev 2010, sdhash (similarity digests)**
- Citation: Vassil Roussev. "Data Fingerprinting with Similarity Digests." *Advances in Digital Forensics VI*, IFIP AICT, 207-226, 2010.
- Year: 2010 | Venue: IFIP AICT (Springer) | Link: https://doi.org/10.1007/978-3-642-15506-2_15 | Verified: yes (R)
- Summary: Selects features by how likely they are to be unique to an object, instead of at random, and builds the tool sdhash. Reports fewer false positives and good scaling.
- How it relates to Pramaan: A second byte-level similarity baseline and a reference for picking distinctive features.
- Its limit for our problem: Features are byte sequences, so a format or capture change breaks matching.

**4.3 Roussev 2011, evaluation of similarity hashes**
- Citation: Vassil Roussev. "An evaluation of forensic similarity hashes." *Digital Investigation*, 8, S34-S41, 2011.
- Year: 2011 | Venue: Digital Investigation (DFRWS 2011) | Link: https://doi.org/10.1016/j.diin.2011.05.005 | Verified: yes (R)
- Summary: Compares ssdeep and sdhash in controlled tests and on real data. Reports that sdhash does better on recall and precision in the scenarios tested.
- How it relates to Pramaan: A model for running a fair similarity-hash benchmark.
- Its limit for our problem: Tests file-level byte similarity only, with no scanned documents.

**4.4 Oliver, Cheng and Chen 2013, TLSH**
- Citation: Jonathan Oliver, Chun Cheng, Yanggui Chen. "TLSH -- A Locality Sensitive Hash." Fourth Cybercrime and Trustworthy Computing Workshop (CTC), 7-13, 2013.
- Year: 2013 | Venue: CTC 2013 (IEEE) | Link: https://doi.org/10.1109/CTC.2013.9 | Verified: yes (R)
- Summary: Notes that one changed byte gives a completely different cryptographic hash. Proposes TLSH, where similar files get similar digests, and compares it with Nilsimsa, ssdeep and sdhash.
- How it relates to Pramaan: The TLSH baseline.
- Its limit for our problem: Byte-level. Gives one distance score and does not say which field changed.

**4.5 Oliver, Forman and Cheng 2014, attacking similarity digests**
- Citation: Jonathan Oliver, Scott Forman, Chun Cheng. "Using Randomization to Attack Similarity Digests." ATIS 2014, CCIS, 199-210, 2014.
- Year: 2014 | Venue: CCIS (Springer) | Link: https://doi.org/10.1007/978-3-662-45670-5_19 | Verified: yes (R)
- Summary: Tests ssdeep, sdhash and TLSH against random changes to several file types. Reports weaknesses in ssdeep and sdhash that are easy to exploit, with TLSH holding up better.
- How it relates to Pramaan: Supports building an adversarial test set and not trusting one similarity score.
- Its limit for our problem: Byte-level attacks only, not document content or legal fields.

**4.6 Pagani, Dell'Amico and Balzarotti 2018, uses and misuses of similarity hashes**
- Citation: Fabio Pagani, Matteo Dell'Amico, Davide Balzarotti. "Beyond Precision and Recall: Understanding Uses (and Misuses) of Similarity Hashes in Binary Analysis." ACM CODASPY, 354-365, 2018.
- Year: 2018 | Venue: ACM CODASPY | Link: https://doi.org/10.1145/3176258.3176306 | Verified: yes (R). Only part of the abstract was seen.
- Summary: Studies how fuzzy hashes such as ssdeep are used to compare program binaries in security and forensics. TODO: verify findings from the full paper before citing any.
- How it relates to Pramaan: A caution that similarity hashes are often used outside the setting they were designed for.
- Its limit for our problem: About executables, not documents.

## 5. Perceptual image hashing

**5.1 Venkatesan et al. 2000, robust image hashing**
- Citation: R. Venkatesan, S.-M. Koon, M. H. Jakubowski, P. Moulin. "Robust image hashing." IEEE ICIP 2000, 664-666, 2000.
- Year: 2000 | Venue: IEEE ICIP | Link: https://doi.org/10.1109/ICIP.2000.899541 | Verified: yes (R)
- Summary: An image hash that uses randomised signal processing to turn an image into a short binary string. Described as robust to compression and geometric distortion and hard to collide on purpose.
- How it relates to Pramaan: Early work on keyed, randomised perceptual hashing, relevant to our stamp and signature hashes (V).
- Its limit for our problem: Works on whole images. Nothing about text content and no explanation of edits.

**5.2 Monga and Evans 2006, feature-point perceptual hashing**
- Citation: Vishal Monga, Brian L. Evans. "Perceptual Image Hashing Via Feature Points: Performance Evaluation and Tradeoffs." *IEEE Transactions on Image Processing*, 15(11), 3452-3465, 2006.
- Year: 2006 | Venue: IEEE TIP | Link: https://doi.org/10.1109/TIP.2006.881948 | Verified: yes (R)
- Summary: Hashes images from visually important feature points, with randomised quantisation to resist attacks. Reports robustness to compression, scaling and small rotations while still detecting malicious content changes.
- How it relates to Pramaan: Close in spirit to our goal of separating harmless changes from real edits, but for images.
- Its limit for our problem: A yes or no decision for a whole image. Does not read text or fields or say what changed.

**5.3 Swaminathan, Mao and Wu 2006, robust and secure image hashing**
- Citation: Ashwin Swaminathan, Yinian Mao, Min Wu. "Robust and secure image hashing." *IEEE Transactions on Information Forensics and Security*, 1(2), 215-230, 2006.
- Year: 2006 | Venue: IEEE TIFS | Link: https://doi.org/10.1109/TIFS.2006.873601 | Verified: yes (R)
- Summary: An image hash from Fourier features with controlled randomness. Measures security as how unpredictable the hash is, and studies the trade-off between security and robustness.
- How it relates to Pramaan: A way to argue that a keyed perceptual hash is secure, not only robust.
- Its limit for our problem: Built for natural images, not text-heavy pages, and gives no location of changes.

**5.4 Zauner 2010, perceptual hash benchmarking (pHash)**
- Citation: Christoph Zauner. "Implementation and Benchmarking of Perceptual Image Hash Functions." Master's thesis, University of Applied Sciences Upper Austria, Hagenberg, 2010.
- Year: 2010 | Venue: Master's thesis | Link: https://www.phash.org/docs/pubs/thesis_zauner.pdf | Verified: yes (P)
- Summary: Builds a benchmark framework and tests four perceptual hashes, including the DCT-based hash. Reports differences in speed and discrimination, and that none of the tested hashes is robust to a horizontal flip.
- How it relates to Pramaan: The standard reference for the DCT pHash used as our whole-page pHash baseline.
- Its limit for our problem: Looks at overall appearance, so a small text edit may barely change the hash.

**5.5 Hao et al. 2021, manipulating perceptual hashing**
- Citation: Qingying Hao, Licheng Luo, Steve T. K. Jan, Gang Wang. "It's Not What It Looks Like: Manipulating Perceptual Hashing based Applications." ACM CCS 2021, 69-85, 2021.
- Year: 2021 | Venue: ACM CCS | Link: https://doi.org/10.1145/3460120.3484559 | Verified: yes (R)
- Summary: Designs black-box attacks that change an image's perceptual hash a lot while barely changing how it looks. Tests them on pHash and on real reverse image search engines.
- How it relates to Pramaan: Evidence that a whole-page pHash alone can be evaded, which motivates our hybrid design and adversarial tests.
- Its limit for our problem: An attack study on general images, not documents.

**5.6 Struppek et al. 2022, breaking NeuralHash**
- Citation: Lukas Struppek, Dominik Hintersdorf, Daniel Neider, Kristian Kersting. "Learning to Break Deep Perceptual Hashing: The Use Case NeuralHash." ACM FAccT 2022, 58-69, 2022.
- Year: 2022 | Venue: ACM FAccT | Link: https://doi.org/10.1145/3531146.3533073 | Verified: yes (P), arXiv 2111.06628 plus Crossref.
- Summary: Studies Apple's NeuralHash and shows that small changes, or even standard image transforms, can force or prevent hash collisions. Also reports that the hashes can leak information about the image.
- How it relates to Pramaan: A direct warning for any learned hash, including our narrative hash. Supports keyed field fingerprints and adversarial tests.
- Its limit for our problem: Images only, and an attack paper.

**5.7 Jain, Cretu and de Montjoye 2022, evading perceptual hashing**
- Citation: Shubham Jain, Ana-Maria Cretu, Yves-Alexandre de Montjoye. "Adversarial Detection Avoidance Attacks: Evaluating the robustness of perceptual hashing-based client-side scanning." USENIX Security 2022, 2317-2334, 2022.
- Year: 2022 | Venue: USENIX Security | Link: https://www.usenix.org/conference/usenixsecurity22/presentation/jain | Verified: yes (P)
- Summary: Presents black-box and white-box attacks on DCT-based perceptual hashing. Reports that almost all test images could be changed to avoid detection while keeping their content.
- How it relates to Pramaan: More evidence that the DCT pHash baseline is weak against deliberate changes.
- Its limit for our problem: The opposite goal (avoiding a match), on photos, not documents.

## 6. Semantic hashing and learning to hash

**6.1 Charikar 2002, SimHash**
- Citation: Moses S. Charikar. "Similarity estimation techniques from rounding algorithms." ACM STOC 2002, 380-388, 2002.
- Year: 2002 | Venue: ACM STOC | Link: https://doi.org/10.1145/509907.509965 | Verified: yes (R)
- Summary: Defines locality sensitive hashes where the chance of a collision equals the similarity of two items. Gives a hash based on random hyperplanes that estimates the angle between vectors.
- How it relates to Pramaan: The theory behind sign-based binary codes compared by Hamming distance, which our narrative hash uses.
- Its limit for our problem: A general result with no notion of documents, edits or explanation.

**6.2 Manku, Jain and Das Sarma 2007, near-duplicate detection**
- Citation: Gurmeet Singh Manku, Arvind Jain, Anish Das Sarma. "Detecting near-duplicates for web crawling." WWW 2007, 141-150, 2007.
- Year: 2007 | Venue: WWW | Link: https://doi.org/10.1145/1242572.1242592 | Verified: yes (R)
- Summary: Shows that SimHash fingerprints work for finding near-duplicate web pages at very large scale, and gives a fast way to find fingerprints within a few bits of a query.
- How it relates to Pramaan: The main SimHash application, and a technique for fast Hamming lookups.
- Its limit for our problem: Designed to treat small differences as irrelevant. In a legal document a small change can be the one that matters.

**6.3 Salakhutdinov and Hinton 2009, semantic hashing**
- Citation: Ruslan Salakhutdinov, Geoffrey Hinton. "Semantic hashing." *International Journal of Approximate Reasoning*, 50(7), 969-978, 2009.
- Year: 2009 | Venue: IJAR (Elsevier) | Link: https://doi.org/10.1016/j.ijar.2008.11.006 | Verified: yes (R)
- Summary: Trains a deep model on word counts so that similar documents get nearby short binary codes. Retrieval then becomes a lookup of codes a few bits away.
- How it relates to Pramaan: The origin of the term "semantic hashing" and of the idea behind our narrative hash.
- Its limit for our problem: Built to find similar documents, not to detect small meaning-changing edits.

**6.4 Wang et al. 2018, survey on learning to hash**
- Citation: Jingdong Wang, Ting Zhang, Jingkuan Song, Nicu Sebe, Heng Tao Shen. "A Survey on Learning to Hash." *IEEE TPAMI*, 40(4), 769-790, 2018.
- Year: 2018 | Venue: IEEE TPAMI | Link: https://doi.org/10.1109/TPAMI.2017.2699960 | Verified: yes (P), arXiv 1606.00185 plus Crossref.
- Summary: Groups learning-to-hash methods by how they keep similarity (pairwise, multiwise, implicit, quantisation) and describes how they are evaluated.
- How it relates to Pramaan: Places our triplet-trained (multiwise) text hash among existing methods.
- Its limit for our problem: Focused on retrieval accuracy, not integrity checking or explaining changes.

**6.5 Chaidaroon and Fang 2017, variational deep semantic hashing for text**
- Citation: Suthee Chaidaroon, Yi Fang. "Variational Deep Semantic Hashing for Text Documents." ACM SIGIR 2017, 75-84, 2017.
- Year: 2017 | Venue: ACM SIGIR | Link: https://doi.org/10.1145/3077136.3080816 | Verified: yes (R)
- Summary: Deep generative models trained by variational inference to produce binary codes for text documents, tested on public datasets.
- How it relates to Pramaan: Direct prior work on deep text hashing.
- Its limit for our problem: Aimed at similarity search. No Indian languages and no edit sensitivity in the abstract.

**6.6 Lai et al. 2015, deep hashing with triplet ranking loss**
- Citation: Hanjiang Lai, Yan Pan, Ye Liu, Shuicheng Yan. "Simultaneous feature learning and hash coding with deep neural networks." IEEE CVPR 2015, 3270-3278, 2015.
- Year: 2015 | Venue: IEEE CVPR | Link: https://doi.org/10.1109/CVPR.2015.7298947 | Verified: yes (R)
- Summary: Learns image features and hash bits together in one deep network, trained with a triplet ranking loss.
- How it relates to Pramaan: The main precedent for training binary codes with a triplet loss, as we do.
- Its limit for our problem: Images and retrieval only. Its triplets mean "same class", not "same legal content".

**6.7 Cao et al. 2017, HashNet**
- Citation: Zhangjie Cao, Mingsheng Long, Jianmin Wang, Philip S. Yu. "HashNet: Deep Learning to Hash by Continuation." IEEE ICCV 2017, 5609-5618, 2017.
- Year: 2017 | Venue: IEEE ICCV | Link: https://doi.org/10.1109/ICCV.2017.598 | Verified: yes (R)
- Summary: Deals with the hard-to-train sign step by starting with a smooth activation and making it sharper during training, so the network learns exact binary codes.
- How it relates to Pramaan: A training technique for the tanh-then-sign step of our narrative hash.
- Its limit for our problem: Image retrieval only.

## 7. Contrastive and metric learning

**7.1 Bromley et al. 1993, siamese signature verification**
- Citation: Jane Bromley, Isabelle Guyon, Yann LeCun, Eduard Säckinger, Roopak Shah. "Signature Verification using a 'Siamese' Time Delay Neural Network." NIPS 6, 1993.
- Year: 1993 | Venue: NIPS | Link: https://proceedings.neurips.cc/paper/1993/hash/288cc0ff022877bd3df94bc9360b9c5d-Abstract.html | Verified: yes (P)
- Summary: Introduces the siamese network: two identical subnetworks whose outputs are compared by distance. A signature is accepted if it is close enough to the stored reference.
- How it relates to Pramaan: The origin of learned pairwise similarity, relevant to both our narrative hash and signature regions.
- Its limit for our problem: Online pen-tablet signatures, not scanned paper. Gives only accept or reject.

**7.2 Hadsell, Chopra and LeCun 2006, contrastive loss**
- Citation: R. Hadsell, S. Chopra, Y. LeCun. "Dimensionality Reduction by Learning an Invariant Mapping." IEEE CVPR 2006, 1735-1742, 2006.
- Year: 2006 | Venue: IEEE CVPR | Link: https://doi.org/10.1109/CVPR.2006.100 | Verified: yes (R)
- Summary: Learns a mapping to a low-dimensional space where similar inputs are close, using only neighbour relations. The mapping can be made to ignore chosen input changes.
- How it relates to Pramaan: The basis of contrastive loss. Learning to ignore chosen changes matches our goal of ignoring scan and format noise.
- Its limit for our problem: Images, real-valued outputs, no edit detection.

**7.3 Schroff, Kalenichenko and Philbin 2015, FaceNet**
- Citation: Florian Schroff, Dmitry Kalenichenko, James Philbin. "FaceNet: A Unified Embedding for Face Recognition and Clustering." IEEE CVPR 2015, 815-823, 2015.
- Year: 2015 | Venue: IEEE CVPR | Link: https://doi.org/10.1109/CVPR.2015.7298682 | Verified: yes (P), arXiv 1503.03832 plus Crossref.
- Summary: Trains a network to map faces into a space where distance reflects similarity, using a triplet loss with online mining of hard examples.
- How it relates to Pramaan: The standard reference for triplet loss and hard example mining, which we use to train the narrative hash.
- Its limit for our problem: Faces only, and real-valued embeddings, not binary text codes.

**7.4 Hermans, Beyer and Leibe 2017, in defense of the triplet loss**
- Citation: Alexander Hermans, Lucas Beyer, Bastian Leibe. "In Defense of the Triplet Loss for Person Re-Identification." arXiv:1703.07737, 2017.
- Year: 2017 | Venue: arXiv preprint | Link: https://doi.org/10.48550/arXiv.1703.07737 | Verified: yes (P)
- Summary: Argues that a well-designed triplet loss trained end to end is a strong choice, and shows it competing well on person re-identification.
- How it relates to Pramaan: Supports our choice of triplet loss with hard negatives.
- Its limit for our problem: Vision task, and a preprint with no peer-reviewed venue listed.

**7.5 Reimers and Gurevych 2019, Sentence-BERT**
- Citation: Nils Reimers, Iryna Gurevych. "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks." EMNLP-IJCNLP 2019, 3982-3992, 2019.
- Year: 2019 | Venue: EMNLP-IJCNLP | Link: https://doi.org/10.18653/v1/D19-1410 | Verified: yes (P)
- Summary: Fine-tunes BERT in siamese and triplet setups so each sentence gets its own embedding that can be compared quickly.
- How it relates to Pramaan: The template for turning a BERT-style encoder (MuRIL for us) into a passage embedder trained with triplets.
- Its limit for our problem: Tuned for semantic similarity, so a changed name or number may still score as "similar". This is the behaviour our training must avoid.

**7.6 Gao, Yao and Chen 2021, SimCSE**
- Citation: Tianyu Gao, Xingcheng Yao, Danqi Chen. "SimCSE: Simple Contrastive Learning of Sentence Embeddings." EMNLP 2021, 6894-6910, 2021.
- Year: 2021 | Venue: EMNLP | Link: https://doi.org/10.18653/v1/2021.emnlp-main.552 | Verified: yes (P)
- Summary: Contrastive sentence embeddings. The supervised version uses contradiction pairs as hard negatives.
- How it relates to Pramaan: Using contradictions as hard negatives is close to our use of minimally edited text (for example added negation) as hard negatives.
- Its limit for our problem: English only, real-valued, and aimed at meaning similarity, not small factual edits.

## 8. Indic language models and Indic OCR

**8.1 Khanuja et al. 2021, MuRIL**
- Citation: Simran Khanuja, Diksha Bansal, Sarvesh Mehtani, Savya Khosla, Atreyee Dey, Balaji Gopalan, Dilip Kumar Margam, Pooja Aggarwal, Rajiv Teja Nagipogu, Shachi Dave, Shruti Gupta, Subhash Chandra Bose Gali, Vish Subramanian, Partha Talukdar. "MuRIL: Multilingual Representations for Indian Languages." arXiv:2103.10730, 2021.
- Year: 2021 | Venue: arXiv preprint | Link: https://doi.org/10.48550/arXiv.2103.10730 | Verified: yes (P)
- Summary: A BERT-style model trained on Indian-language text, with translated and transliterated pairs added. Reports better results than mBERT on the XTREME tasks, including transliterated test sets.
- How it relates to Pramaan: Our main encoder for the narrative hash and the field tagger.
- Its limit for our problem: A general language model, not trained for similarity, hashing or legal text.

**8.2 Kakwani et al. 2020, IndicNLPSuite (IndicBERT)**
- Citation: Divyanshu Kakwani, Anoop Kunchukuttan, Satish Golla, Gokul N.C., Avik Bhattacharyya, Mitesh M. Khapra, Pratyush Kumar. "IndicNLPSuite: Monolingual Corpora, Evaluation Benchmarks and Pre-trained Multilingual Language Models for Indian Languages." Findings of EMNLP 2020, 4948-4961, 2020.
- Year: 2020 | Venue: Findings of EMNLP | Link: https://doi.org/10.18653/v1/2020.findings-emnlp.445 | Verified: yes (P)
- Summary: Releases large text corpora for 11 Indian languages, word embeddings, ALBERT-based models (IndicBERT) and the IndicGLUE benchmark.
- How it relates to Pramaan: The source of the IndicBERT baseline encoder.
- Its limit for our problem: General language understanding, mostly news text. Nothing on legal text or hashing.

**8.3 Doddapaneni et al. 2023, IndicBERT v2 and IndicXTREME**
- Citation: Sumanth Doddapaneni, Rahul Aralikatte, Gowtham Ramesh, Shreya Goyal, Mitesh M. Khapra, Anoop Kunchukuttan, Pratyush Kumar. "Towards Leaving No Indic Language Behind: Building Monolingual Corpora, Benchmark and Models for Indic Languages." ACL 2023, 12402-12426, 2023.
- Year: 2023 | Venue: ACL | Link: https://doi.org/10.18653/v1/2023.acl-long.693 | Verified: yes (P)
- Summary: Releases a larger corpus covering more Indian languages, the IndicXTREME benchmark and the IndicBERT v2 model.
- How it relates to Pramaan: A newer baseline encoder to compare with MuRIL.
- Its limit for our problem: General language understanding, nothing on document integrity.

**8.4 Feng et al. 2022, LaBSE**
- Citation: Fangxiaoyu Feng, Yinfei Yang, Daniel Cer, Naveen Arivazhagan, Wei Wang. "Language-agnostic BERT Sentence Embedding." ACL 2022, 878-891, 2022.
- Year: 2022 | Venue: ACL | Link: https://doi.org/10.18653/v1/2022.acl-long.62 | Verified: yes (P)
- Summary: Multilingual sentence embeddings trained with translation ranking and other objectives, covering over 100 languages.
- How it relates to Pramaan: A baseline encoder, and an example of contrastive multilingual training.
- Its limit for our problem: Built to match translations, not to separate near-identical texts that differ in one fact.

**8.5 Wang et al. 2024, Multilingual E5**
- Citation: Liang Wang, Nan Yang, Xiaolong Huang, Linjun Yang, Rangan Majumder, Furu Wei. "Multilingual E5 Text Embeddings: A Technical Report." arXiv:2402.05672, 2024.
- Year: 2024 | Venue: arXiv technical report | Link: https://doi.org/10.48550/arXiv.2402.05672 | Verified: yes (P)
- Summary: Open multilingual embedding models, contrastively pre-trained on a large set of text pairs and then fine-tuned.
- How it relates to Pramaan: A baseline encoder.
- Its limit for our problem: Aimed at retrieval and similarity, not edit detection.

**8.6 Du et al. 2020, PP-OCR (PaddleOCR)**
- Citation: Yuning Du, Chenxia Li, Ruoyu Guo, Xiaoting Yin, Weiwei Liu, Jun Zhou, Yifan Bai, Zilin Yu, Yehua Yang, Qingqing Dang, Haoshuang Wang. "PP-OCR: A Practical Ultra Lightweight OCR System." arXiv:2009.09941, 2020.
- Year: 2020 | Venue: arXiv preprint | Link: https://doi.org/10.48550/arXiv.2009.09941 | Verified: yes (P)
- Summary: A lightweight OCR pipeline (text detection, direction classification, recognition) released in the PaddleOCR repository.
- How it relates to Pramaan: The paper behind PaddleOCR, one of our two OCR candidates (Phase 6).
- Its limit for our problem: English OCR quality on our documents must be measured in Phase 6.

**8.7 Smith 2007, Tesseract**
- Citation: R. Smith. "An Overview of the Tesseract OCR Engine." ICDAR 2007, vol. 2, 629-633, 2007.
- Year: 2007 | Venue: ICDAR | Link: https://doi.org/10.1109/ICDAR.2007.4376991 | Verified: yes (P), Google Research publication page plus Crossref.
- Summary: Describes the Tesseract OCR engine: line finding, features, classification and its adaptive classifier.
- How it relates to Pramaan: The classic open-source OCR reference point.
- Its limit for our problem: An old engine description with no Devanagari evaluation in the abstract.

**8.8 Mathew, Singh and Jawahar 2016, multilingual OCR for Indic scripts**
- Citation: Minesh Mathew, Ajeet Kumar Singh, C. V. Jawahar. "Multilingual OCR for Indic Scripts." 12th IAPR Workshop on Document Analysis Systems (DAS), 186-191, 2016.
- Year: 2016 | Venue: DAS | Link: https://doi.org/10.1109/DAS.2016.68 | Verified: yes (R)
- Summary: Identifies the script of each word and then recognises it with a segmentation-free recurrent network, across 12 Indian languages and English. Reports that accuracy on Indian languages is lower than on English, and compares Hindi results with other OCR engines.
- How it relates to Pramaan: Prior work on OCR of Indian documents. Pramaan v1 is English only; this becomes direct prior work when Hindi is added (future work).
- Its limit for our problem: OCR accuracy only, and from before current transformer-based OCR.

## 9. Document image forgery and tamper detection

**9.1 Qu et al. 2023, DocTamper (tampered text detection)**
- Citation: Chenfan Qu, Chongyu Liu, Yuliang Liu, Xinhong Chen, Dezhi Peng, Fengjun Guo, Lianwen Jin. "Towards Robust Tampered Text Detection in Document Image: New Dataset and New Solution." IEEE/CVF CVPR 2023.
- Year: 2023 | Venue: CVPR | Link: https://doi.org/10.1109/cvpr52729.2023.00575 | Verified: yes (R)
- Summary: A detector for tampered text that looks visually consistent, including in photographed documents, plus a large dataset of tampered document images (DocTamper). Trained to stay robust under image compression.
- How it relates to Pramaan: A strong pixel-level method for finding edited text regions in a single image.
- Its limit for our problem: Says "this region looks edited", but does not compare with a sealed original or say which legal field changed. An edit that leaves no visual trace is not caught.

**9.2 Bertrand et al. 2013, intrinsic features for fraudulent documents**
- Citation: Romain Bertrand, Petra Gomez-Krämer, Oriol Ramos Terrades, Patrick Franco, Jean-Marc Ogier. "A System Based on Intrinsic Features for Fraudulent Document Detection." ICDAR 2013.
- Year: 2013 | Venue: ICDAR | Link: https://doi.org/10.1109/icdar.2013.29 | Verified: yes (R)
- Summary: Detects forged paper documents without any security feature added at production time, by finding characters that are outliers or suspiciously identical (copy and paste).
- How it relates to Pramaan: Shows that edits can leave traces at character level, supporting field-level checks.
- Its limit for our problem: Needs no original, but cannot tell an innocent rescan from a clean edit with no traces.

**9.3 Ahmed and Shafait 2014, forgery detection from document contents**
- Citation: Amr Gamal Hamed Ahmed, Faisal Shafait. "Forgery Detection Based on Intrinsic Document Contents." 11th IAPR DAS, 2014.
- Year: 2014 | Venue: DAS | Link: https://doi.org/10.1109/das.2014.26 | Verified: yes (R)
- Summary: Learns which parts of documents from one source form a fixed template, then looks for distortions only in those parts.
- How it relates to Pramaan: FIR and charge sheet forms have fixed templates, so the template versus content split is relevant.
- Its limit for our problem: Needs several documents from the same source and targets template distortion, not changed field values.

**9.4 Cruz et al. 2017, local binary patterns for document forgery**
- Citation: Francisco Cruz, Nicolas Sidère, Mickaël Coustaty, Vincent Poulain d'Andecy, Jean-Marc Ogier. "Local Binary Patterns for Document Forgery Detection." ICDAR 2017.
- Year: 2017 | Venue: ICDAR | Link: https://doi.org/10.1109/icdar.2017.202 | Verified: yes (R)
- Summary: Classifies image patches as forged or genuine using texture features and an SVM, with context from neighbouring patches.
- How it relates to Pramaan: A classic forensic method for the "real edit" side.
- Its limit for our problem: Texture cues change with scanner and camera, and there is no link to a sealed original.

**9.5 Eskenazi, Gomez-Krämer and Ogier 2017, OCR stability for hybrid security**
- Citation: Sébastien Eskenazi, Petra Gomez-Krämer, Jean-Marc Ogier. "A Study of the Factors Influencing OCR Stability for Hybrid Security." ICDAR 2017.
- Year: 2017 | Venue: ICDAR | Link: https://doi.org/10.1109/icdar.2017.388 | Verified: yes (R)
- Summary: Argues that stable OCR is the key need when securing documents that exist both on paper and digitally, because unstable OCR makes two copies of the same document look different. Merging look-alike characters helps, but the authors report it is still not stable enough.
- How it relates to Pramaan: The closest prior work to our text-based check. It states the rescan versus edit problem directly.
- Its limit for our problem: Reports that OCR alone is not stable enough. No explanation of changes and no Devanagari.

**9.6 Eskenazi et al. 2017, perceptual image hashing for hybrid document security**
- Citation: Sébastien Eskenazi, Boris Bodin, Petra Gomez-Krämer, Jean-Marc Ogier. "A Perceptual Image Hashing Algorithm for Hybrid Document Security." ICDAR 2017.
- Year: 2017 | Venue: ICDAR | Link: https://doi.org/10.1109/icdar.2017.126 | Verified: yes (R)
- Summary: A hash for the graphical parts of documents on paper and in digital form, designed to stay stable under print and scan noise.
- How it relates to Pramaan: Direct precedent for our stamp and signature region hashes (V).
- Its limit for our problem: Graphics only, with no keyed per-field check and no explanation of changes.

**9.7 Tkachenko et al. 2016, two-level QR code for printed documents**
- Citation: Iuliia Tkachenko, William Puech, Olivier Strauss, Christophe Destruel, Jean-Marc Gaudin. "Printed document authentication using two level QR code." IEEE ICASSP 2016.
- Year: 2016 | Venue: ICASSP | Link: https://doi.org/10.1109/icassp.2016.7472057 | Verified: yes (R)
- Summary: A QR code with textured patterns that degrade when the page is printed and copied, so unauthorised copies can be detected.
- How it relates to Pramaan: Prior work on QR-based checking of paper documents.
- Its limit for our problem: Built to reject copies. We must accept harmless copies and catch content edits.

## 10. Transparency logs and tamper-evident logging

**10.1 RFC 6962, Certificate Transparency**
- Citation: B. Laurie, A. Langley, E. Kasper. "Certificate Transparency." RFC 6962, IETF, 2013.
- Year: 2013 | Venue: IETF RFC (Experimental, obsoleted by RFC 9162) | Link: https://www.rfc-editor.org/info/rfc6962 | Verified: yes (P)
- Summary: Public, append-only logs of TLS certificates built on Merkle trees, so anyone can audit certificate authorities and the logs themselves.
- How it relates to Pramaan: The design model for our action log, signed tree heads and proofs.
- Its limit for our problem: Logs certificates, not document actions. Needs outside monitors to catch a log that shows different views to different people.

**10.2 RFC 9162, Certificate Transparency Version 2.0**
- Citation: B. Laurie, E. Messeri, R. Stradling. "Certificate Transparency Version 2.0." RFC 9162, IETF, 2021.
- Year: 2021 | Venue: IETF RFC (Experimental) | Link: https://www.rfc-editor.org/info/rfc9162 | Verified: yes (P)
- Summary: The updated CT protocol that replaces RFC 6962, with Merkle tree logs and inclusion and consistency proofs.
- How it relates to Pramaan: The current reference for our proof formats. Cite next to RFC 6962.
- Its limit for our problem: Same as RFC 6962.

**10.3 Merkle 1988, hash tree signature**
- Citation: Ralph C. Merkle. "A Digital Signature Based on a Conventional Encryption Function." Advances in Cryptology, CRYPTO '87, LNCS 293, 369-378, Springer, 1988.
- Year: 1988 (CRYPTO '87 proceedings) | Venue: CRYPTO, LNCS | Link: https://doi.org/10.1007/3-540-48184-2_32 | Verified: yes (R). Bibliographic record only, no abstract seen.
- Summary: Known as the paper that introduced hash trees (Merkle trees) to authenticate many values with one root hash. TODO: verify this summary against the paper text.
- How it relates to Pramaan: The origin of the hash tree behind our transparency log.
- Its limit for our problem: A building block, not a log.

**10.4 Crosby and Wallach 2009, tamper-evident logging**
- Citation: Scott A. Crosby, Dan S. Wallach. "Efficient Data Structures for Tamper-Evident Logging." 18th USENIX Security Symposium, 2009.
- Year: 2009 | Venue: USENIX Security | Link: https://www.usenix.org/conference/usenixsecurity09/technical-sessions/presentation/efficient-data-structures-tamper-evident | Verified: yes (P)
- Summary: Treats the logger as untrusted and kept honest by auditors who ask for proofs. A tree structure gives small proofs that an event is in the log and that the log only grew. Names insiders with high-level access as a threat.
- How it relates to Pramaan: Core prior work for "an insider admin cannot silently rewrite the action log".
- Its limit for our problem: Relies on active outside auditors. Says nothing about document content.

**10.5 Schneier and Kelsey 1999, secure audit logs**
- Citation: Bruce Schneier, John Kelsey. "Secure audit logs to support computer forensics." *ACM Transactions on Information and System Security*, 2(2), 159-176, 1999.
- Year: 1999 | Venue: ACM TISSEC | Link: https://doi.org/10.1145/317087.317089 | Verified: yes (R)
- Summary: A low-cost method for logs on a machine that may later be taken over. Entries written before the takeover cannot be read, changed or deleted without detection.
- How it relates to Pramaan: The classic hash-chain approach that our Merkle log with external tree heads improves on.
- Its limit for our problem: Protects only entries written before the compromise, and is not publicly auditable.

**10.6 Melara et al. 2015, CONIKS**
- Citation: Marcela S. Melara, Aaron Blankstein, Joseph Bonneau, Edward W. Felten, Michael J. Freedman. "CONIKS: Bringing Key Transparency to End Users." 24th USENIX Security Symposium, 2015.
- Year: 2015 | Venue: USENIX Security | Link: https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/melara | Verified: yes (P)
- Summary: Applies transparency logs to user key directories, so users can check their own entries and detect a provider that shows different keys to different people.
- How it relates to Pramaan: Shows how to detect a server that gives different views of the log, which supports exporting signed tree heads outside the system.
- Its limit for our problem: Key directories, not action logs or documents.

**10.7 Google Trillian (software)**
- Citation: Google. "Trillian: A transparent, highly scalable and cryptographically verifiable data store." GitHub repository google/trillian, Apache-2.0. Accessed October 2026.
- Year: n/a (software, cite with access date) | Venue: open-source software | Link: https://github.com/google/trillian | Verified: yes (P)
- Summary: A Merkle tree append-only log with inclusion and consistency proofs, used to run Certificate Transparency logs. The README says it is in maintenance mode and points new users to Tessera.
- How it relates to Pramaan: A production reference design for our log.
- Its limit for our problem: Infrastructure only, and in maintenance mode.

## 11. Legal NLP and legal document understanding

**11.1 Chalkidis et al. 2020, LEGAL-BERT**
- Citation: Ilias Chalkidis, Manos Fergadiotis, Prodromos Malakasiotis, Nikolaos Aletras, Ion Androutsopoulos. "LEGAL-BERT: The Muppets straight out of Law School." Findings of EMNLP 2020, 2898-2904, 2020.
- Year: 2020 | Venue: Findings of EMNLP | Link: https://doi.org/10.18653/v1/2020.findings-emnlp.261 | Verified: yes (P)
- Summary: Compares ways of adapting BERT to legal text (use as is, continue pre-training, or train from scratch) and releases LEGAL-BERT models.
- How it relates to Pramaan: Shows that domain adaptation matters for legal text, which supports fine-tuning MuRIL on our documents.
- Its limit for our problem: English only, on EU, UK and US legal text.

**11.2 Zhong et al. 2020, legal AI survey**
- Citation: Haoxi Zhong, Chaojun Xiao, Cunchao Tu, Tianyang Zhang, Zhiyuan Liu, Maosong Sun. "How Does NLP Benefit Legal System: A Summary of Legal Artificial Intelligence." ACL 2020, 5218-5230, 2020.
- Year: 2020 | Venue: ACL | Link: https://doi.org/10.18653/v1/2020.acl-main.466 | Verified: yes (P)
- Summary: Surveys legal AI and contrasts rule-based methods (preferred by legal professionals) with data-driven methods (preferred by NLP researchers).
- How it relates to Pramaan: Places our hybrid of rules (F) and learned models (N) within legal AI.
- Its limit for our problem: Document integrity is not among the tasks covered.

**11.3 Malik et al. 2021, ILDC**
- Citation: Vijit Malik, Rishabh Sanjay, Shubham Kumar Nigam, Kripabandhu Ghosh, Shouvik Kumar Guha, Arnab Bhattacharya, Ashutosh Modi. "ILDC for CJPE: Indian Legal Documents Corpus for Court Judgment Prediction and Explanation." ACL-IJCNLP 2021, 4046-4062, 2021.
- Year: 2021 | Venue: ACL-IJCNLP | Link: https://doi.org/10.18653/v1/2021.acl-long.313 | Verified: yes (P)
- Summary: A corpus of Indian Supreme Court cases for predicting and explaining judgments. Reports that model accuracy and explanations fall well short of legal experts.
- How it relates to Pramaan: A key Indian legal NLP resource. The gap between model and expert supports our "draft for officer review" stance.
- Its limit for our problem: English judgments, not FIRs or charge sheets, and a prediction task.

**11.4 Kalamkar et al. 2022, legal NER on Indian judgments**
- Citation: Prathamesh Kalamkar, Astha Agarwal, Aman Tiwari, Smita Gupta, Saurabh Karn, Vivek Raghavan. "Named Entity Recognition in Indian court judgments." Natural Legal Language Processing Workshop 2022, 184-193, 2022.
- Year: 2022 | Venue: NLLP Workshop | Link: https://doi.org/10.18653/v1/2022.nllp-1.15 | Verified: yes (P)
- Summary: A corpus of annotated legal entities in Indian court judgments, across many legal entity types, with a baseline extraction model.
- How it relates to Pramaan: The closest prior work to our MuRIL field tagger (Phase 13).
- Its limit for our problem: Court judgments, not FIRs or charge sheets. Extracts entities but does not fingerprint or verify them.

**11.5 Kalamkar et al. 2022, rhetorical roles corpus**
- Citation: Prathamesh Kalamkar, Aman Tiwari, Astha Agarwal, Saurabh Karn, Smita Gupta, Vivek Raghavan, Ashutosh Modi. "Corpus for Automatic Structuring of Legal Documents." LREC 2022, 4420-4429, 2022.
- Year: 2022 | Venue: LREC | Link: https://aclanthology.org/2022.lrec-1.470/ | Verified: yes (P)
- Summary: English legal judgments split into segments labelled with rhetorical roles, with baseline models. Shows the roles help summarisation and judgment prediction.
- How it relates to Pramaan: Supports splitting documents into sections before hashing, so changes can be traced to a section.
- Its limit for our problem: English judgments, and about structure, not integrity.

**11.6 Paul et al. 2022, InLegalBERT**
- Citation: Shounak Paul, Arpan Mandal, Pawan Goyal, Saptarshi Ghosh. "Pre-trained Language Models for the Legal Domain: A Case Study on Indian Law." arXiv:2209.06049, 2022. The arXiv comment says it is to appear at ICAIL 2023.
- Year: 2022 (arXiv) | Venue: arXiv; ICAIL 2023 per arXiv comment | Link: https://doi.org/10.48550/arXiv.2209.06049 | Verified: yes (P) for the arXiv version. TODO: verify the ICAIL 2023 DOI and pages on the ACM Digital Library before citing it as ICAIL.
- Summary: Further pre-trains legal BERT models on Indian legal text, and also trains one from scratch with an Indian legal vocabulary, then tests them on Indian legal tasks.
- How it relates to Pramaan: A legal-domain baseline encoder for Indian law.
- Its limit for our problem: Built for judgments and legal text in general, not for police documents or integrity checking.

## 12. Indian systems and standards

**12.1 CCTNS (MHA and PIB)**
- Citation: Ministry of Home Affairs, Government of India. "Crime and Criminal Tracking Network and Systems (CCTNS)" brief, 2018. Also Press Information Bureau (MHA), "Use of CCTNS", 2 February 2021.
- Year: 2018, 2021 | Venue: mha.gov.in, pib.gov.in | Link: https://www.mha.gov.in/sites/default/files/CCTNS_Briefportal24042018.pdf and https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=1694505 | Verified: yes (P)
- Summary: CCTNS was started to connect police stations and computerise FIRs, investigation and charge sheets. The 2021 release gives the number of police stations where it was deployed.
- How it relates to Pramaan: The system where FIRs already live. Pramaan would sit alongside it, not replace it.
- Its limit for our problem: The opened sources describe record keeping and data sharing, not integrity checks on copies.

**12.2 ICJS (MHA and PIB)**
- Citation: Ministry of Home Affairs. "Inter-operable Criminal Justice System (ICJS)" web page. Also PIB Research Unit, "Interoperable Criminal Justice System" factsheet, 23 June 2022.
- Year: 2022 (factsheet) | Venue: mha.gov.in, pib.gov.in | Link: https://www.mha.gov.in/en/commoncontent/inter-operable-criminal-justice-system-icjs and https://static.pib.gov.in/WriteReadData/specificdocs/documents/2022/jun/doc202262367401.pdf | Verified: yes (P)
- Summary: ICJS links police (CCTNS), courts, prisons, forensics and prosecution so data is entered once and shared. NCRB implements it with NIC.
- How it relates to Pramaan: Documents move between these pillars, which is where verifying copies matters.
- Its limit for our problem: About data exchange. The opened sources do not describe content-level verification of copies.

**12.3 e-Sakshya (PIB and MHA)**
- Citation: Press Information Bureau (MHA), release on the launch of e-Sakshya, Nyaya Setu, Nyaya Shruti and e-Summon apps, 4 August 2024. Also MHA, Lok Sabha Unstarred Question No. 1307, answered 3 December 2024.
- Year: 2024 | Venue: pib.gov.in, mha.gov.in | Link: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2041322 and https://www.mha.gov.in/MHA1/Par2017/pdfs/par2024-pdfs/LS03122024/1307.pdf | Verified: yes (P)
- Summary: e-Sakshya is an app developed by NIC for recording photos and video of crime scenes and testimonies and storing them on a server for courts.
- How it relates to Pramaan: The official direction for digital evidence. Pramaan focuses on paper and scanned documents, which sit next to this work.
- Its limit for our problem: The opened sources do not describe how copies of documents are verified.

**12.4 ISO/IEC 27037:2012**
- Citation: ISO/IEC. "ISO/IEC 27037:2012 Information technology, Security techniques, Guidelines for identification, collection, acquisition and preservation of digital evidence." 2012.
- Year: 2012 | Venue: ISO/IEC JTC 1/SC 27 | Link: https://www.iso.org/standard/44381.html | Verified: yes (P). The page says it was reviewed and confirmed in 2018 and is now under review.
- Summary: Guidance for handling potential digital evidence through identification, collection, acquisition and preservation.
- How it relates to Pramaan: Our preservation and custody design is "designed in line with" it.
- Its limit for our problem: A process guideline, with no method for checking a printed copy.

**12.5 NIST SP 800-86**
- Citation: Karen Kent, Suzanne Chevalier, Tim Grance, Hung Dang. "Guide to Integrating Forensic Techniques into Incident Response." NIST SP 800-86, 2006.
- Year: 2006 | Venue: NIST | Link: https://doi.org/10.6028/NIST.SP.800-86 | Verified: yes (P)
- Summary: Practical forensics guidance from an IT viewpoint, covering files, operating systems, network traffic and applications.
- How it relates to Pramaan: A reference for collection, preservation and forensic logging practice.
- Its limit for our problem: Old and IT-focused, and does not cover document copies.

**12.6 ACPO Good Practice Guide for Digital Evidence (v5)**
- Citation: Association of Chief Police Officers (ACPO). "ACPO Good Practice Guide for Digital Evidence", Version 5, March 2012.
- Year: 2012 | Venue: ACPO (UK), listed on the UK policing national standards site | Link: https://knowledgehub.group/web/national-standards/live-standards/-/ddl_display/ddl/71443377/362284494/maximized | Verified: yes (P). TODO: verify who runs this listing site.
- Summary: Sets principles for handling digital evidence with guidance for each stage. The listing says it was reviewed in 2021 and found still current.
- How it relates to Pramaan: Widely cited evidence-handling principles that our audit trail supports.
- Its limit for our problem: UK guidance, process only.

**12.7 Bharatiya Sakshya Adhiniyam, 2023 (Section 63)**
- Citation: Government of India. "The Bharatiya Sakshya Adhiniyam, 2023 (No. 47 of 2023)." Gazette of India Extraordinary, Part II Section 1, 25 December 2023.
- Year: 2023 | Venue: Gazette of India (copy hosted by MHA) | Link: https://www.mha.gov.in/sites/default/files/2024-04/250882_english_01042024_0.pdf | Verified: yes (P)
- Summary: Section 63 is headed "Admissibility of electronic records". Section 63(4) requires a certificate with an electronic record, and the certificate form in the Schedule asks for hash values (it names SHA1, SHA256 and MD5).
- How it relates to Pramaan: The law already expects hash values for electronic records. Our SHA-256 fits this, and our Section 63 output is a draft for officer review only.
- Its limit for our problem: Names exact hash algorithms only. Nothing about printed copies or explaining changes.

**12.8 Bharatiya Nagarik Suraksha Sanhita, 2023**
- Citation: Government of India. "The Bharatiya Nagarik Suraksha Sanhita, 2023 (No. 46 of 2023)." Gazette of India Extraordinary, Part II Section 1, 25 December 2023.
- Year: 2023 | Venue: Gazette of India (copy hosted by MHA) | Link: https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf | Verified: yes (P)
- Summary: The criminal procedure law. It defines audio-video electronic means and requires some procedures (for example search and seizure) to be recorded electronically.
- How it relates to Pramaan: Shows the push toward electronic records of police procedure.
- Its limit for our problem: A procedural law with no technical integrity method.

**12.9 Bharatiya Nyaya Sanhita, 2023**
- Citation: Government of India. "The Bharatiya Nyaya Sanhita, 2023 (No. 45 of 2023)." Gazette of India Extraordinary, 25 December 2023.
- Year: 2023 | Venue: Gazette of India (copy hosted by MHA) | Link: https://www.mha.gov.in/sites/default/files/2024-04/250883_english_01042024.pdf | Verified: yes (P). Title and Act number confirmed; content sections not reviewed.
- Summary: The criminal law that replaced the IPC. Cited for context and its commencement date.
- How it relates to Pramaan: FIRs and charge sheets cite BNS sections, which are a critical field, and the backdating rule depends on its start date.
- Its limit for our problem: Not a technical source.

### Fact check: commencement of the new criminal laws

The commencement date was checked from the Gazette notifications (copies hosted on mha.gov.in), as planned for Phase 25.

| Law | Notification | In force from | Exception stated |
|---|---|---|---|
| BNS, 2023 | S.O. 850(E), dated 23 February 2024 | 1 July 2024 | Section 106(2) not brought into force by this notification |
| BNSS, 2023 | S.O. 848(E), dated 23 February 2024 | 1 July 2024 | The First Schedule entry for BNS section 106(2) |
| BSA, 2023 | S.O. 849(E), dated 23 February 2024 | 1 July 2024 | None stated |

Sources opened:
- https://www.mha.gov.in/sites/default/files/BhartiyaNyayaSanhita_24022024.pdf
- https://www.mha.gov.in/sites/default/files/BharatiyaNagarikSurakshaSanhita_24022024.pdf
- https://www.mha.gov.in/sites/default/files/BharatiyaSakshyaAdhiniyam_24022024.pdf
- PIB, 30 July 2024, says the same: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2039055

The originals on egazette.gov.in were not opened (TODO: verify). The backdating rule in Phase 25 must handle the section 106(2) exception.

---

## Gap table

Rows are approach groups from the sources above. Cells use only what the cited sources show.
- **No** means the cited sources do not show this property. It does not prove a method can never have it.

Indian systems and standards (heading 12) are context, not technical approaches, so they are not rows.

| Approach | Ignores format/capture changes | Catches small content edits | Explains what changed | Verifies without the original | Resists insider log tampering |
|---|---|---|---|---|---|
| Cryptographic hashes, HMAC, signatures, time-stamps (3.1 to 3.7) | No | Yes | No | Partly (needs the exact digital file) | No (time-stamps limit back-dating only) |
| Fuzzy and similarity hashes: ssdeep, sdhash, TLSH (4.1 to 4.6) | No | Partly (score, not a detector) | No | Partly (digest vs digest, needs a digital file) | No |
| Perceptual image hashes (5.1 to 5.7) | Yes (compression, scaling, small rotation) | Partly (small text edits may barely change the hash; open to adversarial attack) | No | Partly (hash only) | No |
| Semantic hashing and sentence embeddings (6.1 to 6.7, 7.5, 7.6, 8.4, 8.5) | Partly (tolerant of small differences, needs OCR first) | No (designed to ignore small differences) | No | Partly (codes only) | No |
| OCR-based hybrid document security (9.5, 9.6) | Partly (OCR stability reported as not enough) | Partly | No | Partly (compact digest) | No |
| Document image forgery detection (9.1 to 9.4) | Partly (one method robust to compression) | Yes, when the edit leaves visual traces | Partly (region, not field) | Yes (single image) | No |
| Copy-detection codes for printed documents (9.7) | No (rejects copies by design) | No | No | Partly (code on the paper) | No |
| Evidence management and blockchain custody (1.1 to 1.4, 2.1 to 2.5) | No | No | No | No | Partly (shared or permissioned ledger) |
| Transparency and tamper-evident logs (10.1 to 10.7) | No | No | No | No | Yes |
| Legal and Indic NLP models (8.1 to 8.3, 11.1 to 11.6) | No | No | No | No | No |
| **Pramaan Legal Hash (design target, not yet a result)** | Target: Yes | Target: Yes | Target: Yes (field and location) | Target: Yes (QR record) | Target: Yes (Merkle log, external tree heads) |

**The gap:** none of the approaches in the cited sources ignores capture changes and also catches small content edits and names the changed legal field. And none links document verification to a tamper-evident custody log that shows when a change happened and who had access.

---

## Unverified, needs checking

These were found but could not be fully confirmed. They are not cited above.

| # | Source | Problem |
|---|---|---|
| U1 | Giova, "Improving chain of custody in forensic investigation of electronic digital systems", IJCSNS, about 2011 | Only seen in other papers' reference lists. No journal or DOI page opened. |
| U2 | Cosic and Baca, "(Im)proving chain of custody and digital evidence integrity with time stamp", MIPRO 2010 | Repository page returned 403. |
| U3 | Turner, "Digital provenance: interpretation, verification and corroboration", Digital Investigation, 2005 | Seen only in search snippets. |
| U4 | Santamaria et al., "Smart Contracts for Managing the Chain-of-Custody of Digital Evidence: A Practical Case of Study", Smart Cities, 2023 | Seen in a search listing only. |
| U5 | Krawetz, dHash ("Kind of Like That"), Hacker Factor blog | Not opened. Grey literature, cite only as a blog post if used. |
| U6 | Breitinger and Baier, "Properties of a similarity preserving hash function and their realization in sdhash", ISSA 2012 | Bibliographic record seen, abstract not seen. |
| U7 | Indyk and Motwani, "Approximate nearest neighbors", STOC 1998 | Bibliographic record only. Full title as usually cited not confirmed. |
| U8 | Broder, "On the resemblance and containment of documents", SEQUENCES 1997 | Bibliographic record only. |
| U9 | Tkachenko, PhD thesis on graphical codes for printed document authentication | Seen in a search listing only. |
| U10 | Original Gazette notifications S.O. 848(E), 849(E), 850(E) on egazette.gov.in | MHA-hosted copies were read instead. |
| U11 | NCRB CCTNS page (ncrb.gov.in) | Returned an error. MHA and PIB pages used instead. |
| U12 | e-Sakshya usage figures in a PIB release | Not opened. Do not quote. |
| U13 | InLegalBERT at ICAIL 2023 (ACM DL record) | Venue known only from the arXiv comment. |

Partly verified items that are cited above but have a TODO: the 1.1 abstract, the 1.3 author list, the 4.6 findings, the 10.3 content and the 12.6 site operator.

## Note for Phase 2 (licences)

While checking sources, the Surya OCR repository (https://github.com/datalab-to/surya) was opened. Its README says the code is Apache 2.0, but the model weights use a modified AI Pubs Open Rail-M licence. That licence is free only for research, personal use and startups below a funding or revenue limit. This needs a decision in Phase 2 against our no-non-commercial rule. PaddleOCR (8.6) may be the safer default. TODO: verify both licences in Phase 2.
