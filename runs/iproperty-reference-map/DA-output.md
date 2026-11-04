# DA — Case Against iProperty Metadata Tagging as Clean Sweeper Reference Map

## 1. Writing to unchecked-out Vault files is a workflow violation with silent consequences

The old source files are not checked out. Writing iProperties to them and saving locally creates a locally-modified file that Vault does not know about. When the user next does a Get Latest or the file is overwritten by another team member's checkin, Vault silently replaces the local copy — the tag is gone with zero warning. Worse: Vault may flag the file as locally modified and block the next Get, forcing a manual "discard local changes" resolution. You are introducing a Vault state conflict on every source file you touch, for a tag that may evaporate before it is ever read. The "temporary" nature of the tag is not controlled — it is at the mercy of Vault's next sync event, which could happen minutes into the operation.

## 2. O(n) open/save/close cycle is prohibitively expensive and crash-prone

An assembly tree of 200 files requires 200 individual Inventor open-save-close cycles to write tags. At 5–15 seconds per file on a loaded Inventor session with network storage, that is 15–50 minutes of tag-writing before a single relink occurs. Each open is a crash surface. If Inventor crashes at file 150, you have 150 files tagged and 50 untagged — a partial map that is worse than no map, because the rule may falsely believe it has complete coverage. The existing RunLog writes a single text file and costs milliseconds.

## 3. Absolute path iProperties are stale by design

`CS_SourcePath = C:\Vault\WIP\PJ00161\...` is correct on one machine, on one day. Drive letter remapping (`V:` vs `C:\Vault`), UNC path vs mapped drive, folder restructuring, project archival — any of these silently invalidate every stored path. The RunLog has the same staleness problem for its text entries, but it is a single file a human can inspect and edit. Stale iProperties are buried inside binary Inventor files and require opening each one to audit or correct.

## 4. iProperty namespace is shared — collision and pollution risk

Inventor's User Defined Properties namespace is flat and unversioned. Any iLogic rule, any third-party tool, any CAD admin can read or write `CS_SourcePath`. There is no schema enforcement. If another rule or a future version of the Clean Sweeper uses the same property name with a different format, you get silent data corruption of the reference map. The RunLog has a defined section format and is owned entirely by Clean Sweeper.

## 5. The proposal does not actually solve the orphan/relink problem better than the RunLog

The original motivation — honouring references across session restarts — is already addressed by the RunLog's `[RENAME_MAP]` section, which persists across sessions without touching any Vault file. The iProperty approach adds complexity, Vault risk, and open/save cost to achieve the same result. For the specific GA-orphan sub-traverse gap, the iProperty on the old file would only help if the old file is opened — but the old file is precisely what you are trying to avoid opening (it is not checked out, touching it creates the Vault conflict described above).

## 6. Strip-out pass adds another O(n) cycle and can be forgotten

The "stripout pass to remove CS_* properties before checkin" is a manual step that is easily skipped under time pressure. If a file with CS_SourcePath pointing to a local working path gets checked into Vault, that path is now permanently embedded in the Vault history of that file, visible to every user who opens it.

## Verdict

The iProperty approach trades a simple, self-contained text file for Vault state conflicts, a 15–50 minute open/save/close cost, path staleness baked into binary files, namespace pollution risk, and a mandatory stripout pass that can be forgotten. It solves no problem the RunLog does not already address, and introduces several the RunLog cannot.
