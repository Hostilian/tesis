import Lean
import Formal.Count
import Formal.Indices
import Formal.Threshold
import Formal.Flags
import Formal.Patches
import Formal.Confusion

/-!
# Axiom audit

A proof with an unfinished step, or one that quietly relies on an extra
assumption, would show up here. The command below walks over every theorem
in the `Formal` library and makes the build *fail* if any of them depends on
anything other than Lean's three standard axioms (`propext`, `Quot.sound`,
`Classical.choice`). Lean records the placeholder for an unfinished proof as
an extra axiom, so an unfinished proof is caught as well.
-/

open Lean Elab Command

/-- Fail the build unless every `Formal.*` theorem uses only standard axioms. -/
elab "#assert_standard_axioms_only" : command => do
  let env ← getEnv
  let allowed : List Name := [``propext, ``Quot.sound, ``Classical.choice]
  let mut checked : Nat := 0
  let mut bad : Array (Name × Name) := #[]
  for (n, ci) in env.constants.toList do
    let some idx := env.getModuleIdxFor? n | continue
    let modName := env.header.moduleNames[idx.toNat]!
    unless (`Formal).isPrefixOf modName do continue
    unless ci matches .thmInfo _ do continue
    if n.isInternal then continue
    let axs ← liftCoreM <| collectAxioms n
    for a in axs do
      unless allowed.contains a do
        bad := bad.push (n, a)
    checked := checked + 1
  unless bad.isEmpty do
    throwError m!"non-standard axioms used: {bad.toList}"
  if checked < 50 then
    throwError m!"only {checked} theorems found; expected at least 50"
  logInfo m!"axiom audit passed: {checked} theorems use only propext / Quot.sound / Classical.choice"

#assert_standard_axioms_only

-- Human-readable spot checks of the headline results.
#print axioms Formal.Indices.ndvi_bounds
#print axioms Formal.Indices.bsi_bounds
#print axioms Formal.Threshold.select_unique
#print axioms Formal.Threshold.firstAtLeast_eq_select
#print axioms Formal.Threshold.select_mono
#print axioms Formal.Flags.count_inc_add_dec
#print axioms Formal.Flags.countFlagged_antitone
#print axioms Formal.Patches.kept_idem
#print axioms Formal.Patches.kept_pixels_le
#print axioms Formal.Confusion.confusion_total
