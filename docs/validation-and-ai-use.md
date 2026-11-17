# Validation and AI use

## Changed-input prediction

Keeping the full sample estimates, the 5.50% annual return objective and the reserve eligibility settings fixed. Raise the minimum reserve share from 4% to 80% of portfolio value. The 75% SGOV / 25% VT starting mix should fail the new floor. I expect the feasible set to shrink to zero. Of the two reserve-eligible funds, SGOV has the higher return estimate, and VT has the highest estimate overall. With only 20% available for VT, even an 80% SGOV / 20% VT mix should come in below 5.50%. If that happens, I would stop the pilot under the tighter rule. There would be no selected mix or volatility to compare.

## Results

The [prediction commit](https://github.com/Mrigna01/FIN439Project2/commit/5e4320622c5c438109794c43b3cbd900791dbf50) was pushed before the 80% scenario ran. The [saved output](../data/lab20-output.txt) has the 4% and 80% cases side by side.

At 4%, the search found 408 feasible mixes out of 1,771. The selected mix was 75% SGOV and 25% VT, with a 5.76% estimated annual return, 3.82% annual volatility and 75% eligible reserves. At 80%, no mix passed both rules. The highest estimated return available at that reserve floor was 5.35%, from 80% SGOV and 20% VT. The pilot would stop under the higher floor.

Equal weight fails the return objective. The 40% USIG / 60% VT benchmark fails the reserve floor. Using the last 36 months moves 15 percentage points from VT to SGOV. Cutting VT's annual estimate by one percentage point keeps the original mix at 5.51%. Applying an illustrative 30 basis points of annual costs takes that mix down to 5.46% net. The search can recover the target in the cost scenario by raising VT to 30%, which would be a separate decision.
