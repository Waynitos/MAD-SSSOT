# Frame Generator copy API assumptions — research challenge

User supplied sources:
- https://forums.autodesk.com/t5/inventor-forum/copy-design-made-with-frame-generator/td-p/7028037
- https://cadsetterout.com/inventor-tutorials/copy-an-autodesk-inventor-design/
- https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Is-it-possible-to-make-a-complete-copy-of-a-frame-generator-assembly-in-Inventor.html
- http://inventortrenches.blogspot.com/2011/03/understanding-autodesk-inventor-frame.html

## Claims to validate, not assume
1. Derived skeleton geometry and Frame Generator-specific metadata can be damaged by naive File.SaveAs / ComponentOccurrence.Replace workflows.
2. New copies can retain old skeleton or frame-member references.
3. Frame member GUIDs and hidden XML/manifest structures are involved: **unverified implementation claim**; do not inspect/modify undocumented structures as a repair strategy.
4. Vault API and Autodesk Design Assistant: verify exact Inventor 2025 supported interfaces and automation capabilities; do **not** assume an Inventor `DesignAssistant` object exists.
5. Supported UI workflows (iLogic Design Copy, Vault Copy Design, Design Assistant) are comparison baselines, not necessarily accessible as callable APIs.

## New diagnostic acceptance criteria
- On a disposable minimal frame, capture source/target document reference graphs before and after each copy method.
- Compare opening, saving, frame member editability, end treatments, derived/adaptive skeleton behavior and update propagation after master sketch changes.
- Log any save-context prompts and Vault status independently.
- Record API availability and documented limitations with citations to official Inventor 2025 SDK/API reference.
- Do not implement raw SaveAs/Replace-based repair as production until tests prove frame metadata and associativity survive.
- Preserve separate local diagnostic harness and isolated v2.2.34 branch.
