# Third-party notices and source attribution

IndieDuck by Armature AI Labs, adapted from Open Duck Mini and inspired by Pollen Robotics' MicroDuck.

Copyright 2026 Armature AI Labs for our engineering modifications. Our independently authored contributions and documentation are offered under Apache-2.0, whose text is included below. This grant does not extend to underlying third-party geometry or replace its source-specific terms. This R20 CAD study combines separately authored structure and interfaces, inherited geometry, and our changes. It is not covered by a single blanket Apache-2.0 grant. The retained upstream texts below apply to their respective material; public availability does not supply any missing upstream permission. No sponsorship, endorsement or trademark rights are asserted.

## Source scope

| Source | Pinned revision | Included or referenced material | Recorded terms |
| --- | --- | --- | --- |
| [Open Duck Mini](https://github.com/apirrone/Open_Duck_Mini) by Antoine Pirrone and contributors | `b23317a485b3cec7d8417f352478778b3475173c` | Retained native source history and adapted covers; Jaime Machuca's BD-X-style body-cover mod and Justin Andrews' Park Head mod are credited below. | Apache-2.0, text retained below. |
| [XGO-Duck hardware](https://github.com/LuwuDynamics/xgoduck_hardware) by Luwu Dynamics and upstream contributors | `8b355c6fc374ff7f2921bf78b4880c2b38c57b07` | Head shell, upper bill, jaw, upper/lower lips and retained support source geometry. R20 adds a separate band and shell mounting holes; earlier IndieDuck revisions changed the face, mounting, jaw support and yaw relief. | No finalized source-specific redistribution grant was established in the inspected snapshot. The snapshot's LICENSING and UPSTREAM texts are retained below. This geometry is not newly labelled Apache-2.0. |
| [MicroDuck / microduck_rl](https://github.com/pollen-robotics/microduck_rl) by Pollen Robotics | model reference `273afe0b31c4ab365b9ff806a927b63ac92b5ddd` | Robot inspiration and numerical joint, stance, foot and roller references. No original Pollen mesh files or policies are directly bundled. XGO's recorded Pollen lineage remains applicable to inherited XGO geometry. | Pinned repository distinguishes Apache-2.0 software from its model terms. Software permission is not asserted as a CAD grant. |
| Radxa ZERO 3W and Pollen RPI Robot HAT | Radxa V1.11 mechanical reference; HAT `78f60f711f519e8b57c4b1ea937bd2bb8249b1d3` | Numerical outline, mounting and component-envelope facts represented as reference shapes. | Original Radxa CAD and the HAT STEP's embedded Raspberry Pi model are not included. |
| Feetech HD-1910-C001 documentation | drawing/specification referenced in the project source register | Numerical servo interfaces and simplified hardware reference envelopes. | Manufacturer documentation is not relabelled as IndieDuck CAD. |

Armature contributions include the HD-1910 structure and interface features, compact joint supports, adapted covers, two-eye face and eye rings, foot studies, the upper-bill yaw clearance, and the removable rear band with internal mounting. An independently authored modification does not relicense underlying geometry. Hidden source features retained for editability are not an additional current print list.

For the active part-to-native-object mapping and material classification, use the package manifest. STEP/STL files inherit the provenance of their corresponding native objects. Assembly and review files combine those objects and do not broaden their permissions.

## Preserved contributor attribution

The following contributor README texts are reproduced verbatim from the pinned Open Duck Mini snapshot. Image links and references inside them describe the original upstream package, not files or verified print settings in this release.

### Jaime Machuca (jmachuca77)

```text
# Jaime's V2 BD‑X Style Body Covers Mod

![3D Model Overview](./3D%20Model.png)

Author: Jaime Machuca (jmachuca77)

## Purpose
This is an alternative set of v2 body/head cover parts for Open Duck Mini intended to more closely match the Disney BD‑X aesthetic and surface "skin" lines.

## Important Note on Balance & RL Policy
These covers shift the overall mass distribution and do not perfectly match the original center of gravity assumptions used when training the current reinforcement learning (RL) locomotion policy. The existing policy still works, but may exhibit slightly reduced stability (e.g. more wobble, occasional recovery steps). Monitor performance; if instability becomes an issue, consider fine‑tuning or retraining with updated inertial parameters.

## Printing Guidance
The file `Bambu_X1C_Project_File.3mf` contains suggested part orientations, plate groupings, and baseline settings optimized for a Bambu Labs X1C printer.

Recommended starting points (adjust to your material):
- Material: PETG or PLA-CF (for durability)
- Layer Height: 0.20 mm (features) / 0.28 mm (large flat shells optional)
- Infill: 15–20% gyroid or cubic
- Walls: 3 perimeters for strength on structural covers
- Supports: Only where unavoidable (check project file flags)
- Adhesion: Skirt or minimal brim for tall narrow pieces

![Print Orientation Reference](./Print%20Orientation%20Reference.png)

## Included Parts
Representative filenames (see folder for full list):
- Front/Back/Side body covers (`Front Cover.3mf`, `Back Panel.3mf`, `trunk_*`) 
- Leg covers and cable guides (`Left Leg Cover.3mf`, `Right Leg Cover.3mf`, upper/lower guides) 
- Greebles & panels (`Front Greeble.3mf`, `Front Panel V4.3mf`) 
- Safety / accessory plates (`E-Stop Panel.3mf`, `E-Stop Adapter Plate.3mf`) 
- Assembly helpers (`Hip Cable Holder.3mf`, `Top Body Support.3mf`)

## Usage & Attribution
Feel free to remix or adapt. Please retain attribution to Jaime Machuca (jmachuca77) and reference that this mod targets a closer Disney BD‑X visual style.

## Future Suggestions
- Retrain or fine‑tune RL policy with updated CAD mass properties.

---
If you encounter issues or improved orientations, open a PR or add notes here.
```

### Justin Andrews (Codezombie23)

```text
# Justin's Park Head Mod (BD‑X Style)

This mod updates the Open Duck Mini v2 head to more closely resemble the Disney BD‑X design.

![Park Head Mod Preview](./Park_Head.png)

- Author: Justin Andrews (Codezombie23)
- Project: Open Duck Mini v2 head mod

If you use or remix this, please credit the author above.
```

## Preserved XGO source notices

These are the inspected source snapshot texts. Their internal links refer to the upstream project; they are not an IndieDuck permission grant.

### XGO LICENSING.md

```text
# Licensing status

No top-level license file was found in the repository snapshot used for this documentation update. Publication of files by itself does not establish a complete reuse grant. Upstream and third-party components retain their applicable terms.

## Maintainer intent for eligible original material

The maintainer intends to allow personal and educational replication and require separate authorization for commercial use of material they have the right to license. This statement records intent; it is not a finalized replacement license and does not override any existing grants or third-party rights. File-level scope and final terms are pending.

A project-wide “noncommercial only” label would be inaccurate where Apache-2.0 or another license already permits commercial use. Noncommercial restrictions also do not meet the OSI definition of open-source software. Describe the actual license of each component rather than claiming the whole project is under one permissive license.

For a commercial enquiry, email **hello@xgorobot.com** with the files/revisions involved, intended product or service, expected quantity and distribution plans. For personal/educational replication of material without final terms, use the same address to confirm applicable permissions.

## Design and model provenance

Code licensing does not establish rights to every model or design asset. Review the upstream findings and file-level scope in the hardware repository's [origins documentation](https://github.com/LuwuDynamics/xgoduck_hardware) before distributing inherited designs. Exact source revisions and applicable notices remain to be recorded.

## Credits

The project builds on [Microduck](https://github.com/pollen-robotics/microduck) and [microduck_rl](https://github.com/pollen-robotics/microduck_rl) by Pollen Robotics. Training uses [mjlab](https://github.com/mujocolab/mjlab) and [BAM](https://github.com/Rhoban/bam). Hardware and software adaptations should be credited without implying endorsement by those projects or Arduino.

References: [OSI Open Source Definition](https://opensource.org/osd), [Apache-2.0 text](https://www.apache.org/licenses/LICENSE-2.0).
```

### XGO UPSTREAM.md

```text
# Origins and adaptations

[Project](readme.md) · [Licensing](LICENSING.md)

XGO-Duck is a substantial adaptation of the Microduck ecosystem, not an independently originated robot concept. The maintainer has confirmed extensive reference to Microduck materials. The XGO-Duck repository descriptions also identify that lineage. This page records the architectural relationship; it is not a completed file-by-file copyright audit.

## Credit the foundation

- [Microduck, Pollen Robotics](https://pollen-robotics.com/microduck/): the robot concept and upstream project.
- [Microduck runtime](https://github.com/pollen-robotics/microduck): upstream onboard software and system reference.
- [microduck_rl](https://github.com/pollen-robotics/microduck_rl): upstream learning environments and sim-to-real approach.
- [mjlab](https://github.com/mujocolab/mjlab): training framework.
- [BAM, Rhoban](https://github.com/Rhoban/bam): actuator modelling.

## What follows upstream and what is adapted

| Area | Inherited or referenced foundation | XGO-Duck adaptation documented in its source |
| --- | --- | --- |
| Robot form | Duck-shaped biped with articulated legs, neck, head and mouth | Printable XGO-Duck structure and assembly drawings |
| Joint layout | Fifteen servos and retained policy ordering | Feetech 1910 bus integration and per-robot encoder calibration |
| Learning | Microduck task recipes and PPO/ONNX workflow | XGO-Duck geometry/inertias and HLS1910 BAM parameters |
| Control interface | Shared policy conventions and motion concepts | Linux policy host plus STM32 control on Uno Q |
| Electronics | Reference robot architecture | Luwu expansion board with QMI8658A, power and servo interfaces |

“Adaptation” here describes the engineering work visible in the XGO-Duck source. It does not establish exclusive ownership of every file. The exact upstream base revision, copied paths, original design sources and permissions must still be recorded.

## Compatibility is a separate question

Use the XGO-Duck task IDs, dependencies and deployment instructions in these repositories. Do not substitute an upstream policy solely because its tensors have the same dimensions. Actuator dynamics, geometry, calibration, command meaning and runtime behavior must also agree.

Upstream commands such as `robotctl` belong to a different runtime. They are not XGO-Duck Uno Q installation instructions. Features demonstrated on an upstream robot are not evidence that this hardware variant supports them.

## Model and design rights need their own record

The current [upstream RL README](https://github.com/pollen-robotics/microduck_rl) distinguishes its code license from a noncommercial, share-alike statement for 3D models. Preserve the applicable terms for the actual inherited files and versions; obtain the precise license text and provenance before redistributing derivatives. A code LICENSE alone is insufficient evidence for model rights.

The official [Microduck press kit](https://pollen-robotics.com/microduck/press-kit/) also limits its open-source statement to software. Do not infer design-file permissions from product marketing. These observations were reviewed on 2026-09-26 and are not a finding that any specific XGO-Duck file is unauthorized.

## Attribution for articles and demonstrations

Suggested credit: **“XGO-Duck by Luwu Dynamics, based on Microduck and microduck_rl by Pollen Robotics.”** Add mjlab and Rhoban BAM when discussing training. Preserve file-level copyright and license notices in source distributions. This project does not claim endorsement by Pollen Robotics, Hugging Face, Rhoban or Arduino.
```

## Apache License 2.0 text for the Open Duck Mini material and separately designated Armature material

```text
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright [yyyy] [name of copyright owner]

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```


## Native source mapping


The integrated R20 assembly preserves the R19 robot's datums and structural geometry, replaces the shell with its R20 mounting-hole variant, and adds the R20 removable band. R19 itself builds on R18 structural changes. Do not identify these inherited parts as newly redesigned in R20.

## Imported XGO geometry retained in the native history

Source repository: https://github.com/LuwuDynamics/xgoduck_hardware

Pinned revision: `8b355c6fc374ff7f2921bf78b4880c2b38c57b07`.

| Original file | Retained source object | Current role |
| --- | --- | --- |
| `head_shell.stl` | `XGO_HeadShell_Original`, `XGO_HeadShell_Aligned` | Basis of the modified shell; R20 mounted shell adds two screw holes. |
| `head.stl` | `XGO_head_Source` | Basis of the fastened upper bill and R19 yaw-relief feature. |
| `jaw.stl` | `XGO_jaw_Source` | Basis of the repaired active jaw. |
| `head_servo_support.stl` | `XGO_head_servo_support_Source` | Hidden retained history; superseded by the active IndieDuck cradles. |
| `mouth_up_tpu.stl` | `XGO_mouth_up_tpu_Source` | Active upper lip. |
| `mouth_buttom_tpu.stl` | `XGO_mouth_buttom_tpu_Source` | Active lower lip; source spelling retained. |

Those source STL shapes were converted into faceted B-reps, so editability does not mean every imported surface has an independent dimensioned feature history. Original IndieDuck feature trees, spreadsheets and Boolean modifications remain editable. The two-eye face follows the inherited head boundary and is a source-derived adapter. Native files retain hidden geometry needed for history; only active assembly objects belong in the current part list.

## Active printable classification

Initial rigid fit tests: PLA. Soft soles and lips: TPU 95A. Eye inserts are cosmetic aperture parts, not optical lenses; the camera lens and other bought hardware are reference geometry. All material choices remain prototype choices, not strength or print certification.

The active structural print set is the 39 visible non-reference R19 links preceding R18 hardware, plus the R18 neck-bearing retainer, with the shell replaced and the R20 removable band added: 41 physical printed-piece entries including left/right counterparts. The final component manifest records these 41 entries.

Exclude from printable-part exports: all `A_ref_*` items; hidden head-core/cap and crank-linkage alternatives; R18 bearing, idler, shoulder-pin, metal-spacer, screw and nut objects. Preserve their assembly reference shapes and distinguish any custom metal item still requiring manufacture or sourcing.

## Attribution scope

Open Duck Mini adapted source history includes Antoine Pirrone and contributors, Jaime Machuca's BD-X-style cover mod, and Justin Andrews' Park Head mod. Credit remains even when an older source feature is hidden. Pollen Robotics' MicroDuck supplies inspiration and numerical references. XGO's own source records Pollen lineage. Read THIRD_PARTY_NOTICES.md for the pinned records and preserved notices.
