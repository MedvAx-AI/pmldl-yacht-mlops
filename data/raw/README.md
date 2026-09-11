# Dataset provenance

- Name: Yacht Hydrodynamics, UCI dataset 243.
- Creators: J. Gerritsma, R. Onnink, A. Versluis (1981).
- Source: https://archive.ics.uci.edu/dataset/243/yacht+hydrodynamics
- DOI: https://doi.org/10.24432/C5XG7R
- Download: https://archive.ics.uci.edu/static/public/243/yacht+hydrodynamics.zip
- Retrieved: 2026-09-11.
- License: Creative Commons Attribution 4.0 International, https://creativecommons.org/licenses/by/4.0/.
- Raw file: `yacht_hydrodynamics.data`, redistributed unchanged.
- SHA-256: `00dfecc0fc01ddd4c90b558a3ac11b246df8ebcfea130724223475a9a67f0ea1`.

The file has no header; columns are buoyancy position, prismatic coefficient, length/displacement ratio, beam/draught ratio, length/beam ratio, Froude number, and residuary resistance per unit displacement weight. All are dimensionless. There are 308 rows and 22 hull geometries. The target is retained on its original numeric scale, with no assumed conversion to force units.

Generated cleaned splits are adaptations of this file. No synthetic rows are added to the training data. Corrupt samples appear only in tests.
