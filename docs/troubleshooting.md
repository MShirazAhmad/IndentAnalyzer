# Troubleshooting

## File does not load

Check that the file is an Agilent G200 `.xls` or `.xlsx` export containing full load–displacement curves rather than summary-only data.

## Fit passes but the curve looks wrong

Do not rely on $R^2$ alone. Open the individual test plot and inspect the loading and unloading behavior. Exclude tests affected by pores, surface roughness, poor contact, pile-up or sink-in artifacts, or abnormal curve shape.

## Final averages change after excluding a test

This is expected. The application recalculates mean, standard deviation, and coefficient of variation using only the tests currently included in the final result set.

## Calibration looks inconsistent

Revisit the fused-silica calibration file and inspect the calibration reliability panel before analyzing unknown samples. Downstream hardness and modulus values depend on the selected area function.

## Export is unavailable

Export actions require at least one included result. If you have excluded all tests, re-include a valid test or rerun the analysis.
