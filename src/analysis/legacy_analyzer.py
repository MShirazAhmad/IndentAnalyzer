from pathlib import Path
import pandas as pd
import os
import numpy as np
import matplotlib
# matplotlib.use('Agg')
from scipy.optimize import minimize, minimize_scalar, curve_fit
from matplotlib.patches import Rectangle
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


class IndentXLSAnalyzer:
    from pathlib import Path
    import os
    import numpy as np
    from scipy.optimize import minimize, minimize_scalar
    from matplotlib.patches import Rectangle
    from matplotlib import pyplot as plt
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    import pandas as pd

    pd.options.mode.chained_assignment = None  # Disable SettingWithCopyWarning

    def __init__(self, filename="Silica.xls", optimal_coeffs=None):
        """
        Initialize the IndentXLSAnalyzer with a filename and optimal coefficients.

        Parameters:
        - filename (str): The path to the Excel file containing indentation data.
        - optimal_coeffs (list or None): Initial guess for optimal coefficients [C0, C1, C2, C3].
                                         If None, default coefficients are used.
        """
        self.filename = filename
        self.plottitle = "{} - Test {}, {} GPa (CSM), {} GPa (Oliver-Pharr)"
        self.epsilon = 0.75
        self.Silica_E = 72e9
        self.export = True
        self.pltshowoutput = False
        self.hidePlot = True
        self.optimal_coeffs = optimal_coeffs if optimal_coeffs is not None else [24, 0.000003, 3.431001e-08,
                                                                                   -9.983269e-10]
        self.derivative_threshold = 0.03
        self.deviationFunction = "CalculateR_2" # "CalculateMAE", "CalculateMSE", "CalculateMAPE"
        self.tipCalibration = False
        self.generatePlot = False



    def oliver_pharr_model1(self, h, A, n, hf):
        """
        Oliver-Pharr model function for nanoindentation analysis.

        Parameters:
        h (float): Displacement (nm)
        A (float): Fitting parameter (units depend on the specific application)
        n (float): Fitting parameter (dimensionless)
        hf (float): Final displacement (nm)

        Returns:
        float: Load (mN) calculated using the Oliver-Pharr model
        """
        # Calculate load using the Oliver-Pharr model
        # A is a scaling factor, n is an exponent, and hf is the final displacement
        return A * (h - hf) ** n

    def oliver_pharr_model(self,x, A, hf, n):
        return A * (x - hf) ** n

    def oliver_pharr_fit(self,x, y):
        popt, _ = curve_fit(self.oliver_pharr_model, x, y)
        return popt






    def run_analysis(self):

        # Read the Results sheet
        df_Results = pd.read_excel(self.filename, sheet_name="Results")

        # Iterate through the specified test sheet names
        all_results = []

        for i in [f"0{str(i).zfill(2)}" for i in range(1, 21)]:
            try:
                hardnessCSM = df_Results[df_Results.Test == str(int(i))]["H Average Over Defined Range"].iloc[0]

                # Load test data, dropping the first two rows to match the original structure
                df = pd.read_excel(self.filename, sheet_name=f"Test {i}").drop(index=[0, 1])
                df['Displacement Into Surface'] = pd.to_numeric(df['Displacement Into Surface'], errors='coerce')
                df['Load On Sample'] = pd.to_numeric(df['Load On Sample'], errors='coerce')
                df.dropna(subset=['Displacement Into Surface', 'Load On Sample'], inplace=True)
                peak_index = df["Load On Sample"].idxmax()
                df_before_peak = df.iloc[:peak_index + 1]

                load_threshold = 40  # Adjust based on requirements
                filtered_df = df[df['Load On Sample'] > load_threshold].copy()
                filtered_df['Load Derivative'] = np.gradient(filtered_df['Load On Sample'],
                                                             filtered_df['Displacement Into Surface'])

                is_horizontal = abs(filtered_df['Load Derivative']) < self.derivative_threshold

                start_index = None
                for j in is_horizontal.index:
                    if is_horizontal.loc[j] and start_index is None:
                        start_index = j
                    elif not is_horizontal.loc[j] and start_index is not None:
                        end_index = j
                        start_disp = filtered_df.loc[start_index, 'Displacement Into Surface']
                        end_disp = filtered_df.loc[end_index, 'Displacement Into Surface']
                        df_loading = df[:start_index]
                        df_unloading = df[end_index:]
                        start_index = None  # Reset for next segment
                horizontal = (end_disp - start_disp)
                df_unloading.loc[:, 'Displacement Into Surface'] = df_unloading[
                                                                       'Displacement Into Surface'] - horizontal

                coeffs_loading = np.polyfit(df_before_peak['Displacement Into Surface'],
                                            df_before_peak['Load On Sample'],
                                            2)
                coeffs_unloading = np.polyfit(df_unloading['Displacement Into Surface'], df_unloading['Load On Sample'],
                                              2)
                coeffs_elastic_unloading = np.polyfit(df_unloading['Displacement Into Surface'][:20],
                                                      df_unloading['Load On Sample'][:20], 1)

                x_intersection_point, y_intersection_point = self.find_closest_intersection_point(coeffs_loading,
                                                                                                  coeffs_unloading,
                                                                                                  coeffs_elastic_unloading)
                #"CalculateR_2"  # "CalculateMAE", "CalculateMSE", "CalculateMAPE"
                # Calculate R^2
                r_squared_loading = self.CalculateMAPE(df_before_peak['Displacement Into Surface'],
                                                      df_before_peak['Load On Sample'], coeffs_loading)
                r_squared_unloading = self.CalculateMAPE(df_unloading['Displacement Into Surface'],
                                                        df_unloading['Load On Sample'], coeffs_unloading)

                # Generate sequence for plotting
                x_intercept_unloading = max(np.roots(coeffs_unloading))
                x_poly_unloading = np.linspace(max(np.roots(coeffs_unloading)), x_intersection_point, 100)
                y_poly_unloading = np.polyval(coeffs_unloading, x_poly_unloading)
                x_poly_loading = np.linspace(df_before_peak['Displacement Into Surface'].min(), x_intersection_point,
                                             100)
                y_poly_loading = np.polyval(coeffs_loading, x_poly_loading)

                # Elastic Unloading
                poly = np.poly1d(coeffs_elastic_unloading)
                x_intercept_elastic_unloading = max(np.roots(coeffs_elastic_unloading))
                x_fit_elastic_unloading = np.linspace(x_intercept_elastic_unloading, x_intersection_point, 100)
                y_fit_elastic_unloading = poly(x_fit_elastic_unloading)

                # area_loading = np.trapz(y_poly_loading - y_poly_unloading, x_poly_loading)
                plt.fill_between(x_poly_loading,y_poly_unloading, y_poly_unloading, alpha=0.5, label='Loading Area')

                # area_elastic_unloading = np.trapz(y_poly_unloading - y_fit_elastic_unloading, x_fit_elastic_unloading)
                plt.fill_between(x_fit_elastic_unloading, y_poly_unloading, y_fit_elastic_unloading, alpha=0.5,
                                 label='Elastic Unloading Area')
                # plt.annotate(f'Loading Area: {np.round(area_loading, 2)}', xy=(0.6, 0.8), xycoords='axes fraction')
                # plt.annotate(f'Elastic Unloading Area: {np.round(area_elastic_unloading, 2)}', xy=(0.6, 0.75),
                #              xycoords='axes fraction')

                Pmax = y_intersection_point * 1e-3
                Hmax = x_intersection_point * 1e-9

                S = coeffs_elastic_unloading[0] * 1e6
                Hc = abs(Hmax - self.epsilon * (Pmax / S))
                Hs = x_intercept_elastic_unloading * 1e-9
                Er = self.compute_reduced_modulus(self.Silica_E)

                if self.tipCalibration:
                    self.optimal_coeffs = self.optimize_tip_coeffs(Hc, S, Er, self.optimal_coeffs)

                A = self.Contact_area_from_coefficients(Hc, self.optimal_coeffs)

                Ap = self.calculate_contact_area(S, Er)
                GPa = (Pmax / A) * 1e-9

                if self.tipCalibration:
                    results = {
                        "Test": i,
                        "Pmax (N)": Pmax,
                        "Hmax (m)": Hmax,
                        "S (N/m)": S,
                        "Hc (m)": Hc,
                        "Hs (m)": Hs,
                        "Er (Pa)": Er,
                        "A (m^2)": A,
                        "Ap (m^2)": Ap,
                        "DeltaA": abs(A - Ap),
                        "C0": self.optimal_coeffs[0],
                        "C1": self.optimal_coeffs[1],
                        "C2": self.optimal_coeffs[2],
                        "C3": self.optimal_coeffs[3],
                        "Hardness (GPa)": GPa,
                    }
                else:
                    results = {
                        "Test": i,
                        "Pmax (N)": Pmax,
                        "Hmax (m)": Hmax,
                        "S (N/m)": S,
                        "Hc (m)": Hc,
                        "Hs (m)": Hs,
                        "Er (Pa)": Er,
                        "A (m^2)": A,
                        "Ap (m^2)": Ap,
                        "Hardness (GPa)": GPa,
                    }
                # Append results
                all_results.append(results)

                # Plotting
                if self.generatePlot:
                    plt.figure(figsize=(10, 6))
                    if self.hidePlot:
                        plt.ioff()
                    df_unloading_sample = df_unloading
                    plt.scatter(df_unloading_sample["Displacement Into Surface"], df_unloading_sample["Load On Sample"],
                                edgecolors='orange', facecolors='none', marker='o')
                    df_loading_sample = df_loading
                    plt.scatter(df_loading_sample["Displacement Into Surface"], df_loading_sample["Load On Sample"],
                                edgecolors='orange', facecolors='none', marker='o')
                    plt.plot(x_poly_loading, y_poly_loading, '-', label=f'Loading Fit MAE: {r_squared_loading:.3f}')
                    plt.plot(x_poly_unloading, y_poly_unloading, '-',
                             label=f' Unloading Fit MAE: {r_squared_unloading:.3f}')
                    plt.plot(x_fit_elastic_unloading, y_fit_elastic_unloading, '-')
                    plt.annotate('$h_c$: {}'.format(np.round(Hc * 1e9, 2)),
                                 xy=(Hc * 1e9, 0), xytext=(Hc * 1e9, 12),
                                 arrowprops=dict(facecolor='black', width=1, headwidth=7, headlength=7))
                    plt.annotate('$h_s$: {}'.format(np.round(Hs * 1e9, 2)),
                                 xy=(Hs * 1e9, 0), xytext=(Hs * 1e9, 25),
                                 arrowprops=dict(facecolor='black', width=1, headwidth=7, headlength=7))
                    plt.annotate('$h_e$: {}'.format(np.round(x_intercept_unloading)),
                                 xy=(x_intercept_unloading, 0), xytext=(x_intercept_unloading, 35),
                                 arrowprops=dict(facecolor='black', width=1, headwidth=7, headlength=7))
                    plt.annotate('$S$: {} N/m'.format(np.round(S, 2)),
                                 xy=(np.average(df_unloading['Displacement Into Surface'][:10]),
                                     np.average(df_unloading['Load On Sample'][:10])),
                                 xytext=(np.average(df_unloading['Displacement Into Surface'][:10]) - 300,
                                         np.average(df_unloading['Load On Sample'][:10])),
                                 arrowprops=dict(facecolor='black', width=1, headwidth=7, headlength=7))

                    area_loading = np.abs(
                        np.trapz(y_poly_loading - np.interp(x_poly_loading, x_poly_unloading, y_poly_unloading),
                                 x_poly_loading))
                    area_elastic_unloading = np.abs(np.trapz(
                        y_fit_elastic_unloading - np.interp(x_fit_elastic_unloading, x_poly_unloading,
                                                            y_poly_unloading), x_fit_elastic_unloading))
                    total_area = abs(area_loading) + abs(area_elastic_unloading)
                    loading_area_fraction = round((area_loading / total_area) * 100, 2)
                    unloading_area_fraction = round((area_elastic_unloading / total_area) * 100, 2)

                    plt.fill_betweenx(y_poly_loading, x_poly_loading,
                                      np.interp(y_poly_loading, y_poly_unloading, x_poly_unloading), color='blue',
                                      alpha=0.3, label="Elastic {}%".format(loading_area_fraction))

                    plt.fill_betweenx(y_fit_elastic_unloading, x_fit_elastic_unloading,
                                      np.interp(y_fit_elastic_unloading, y_poly_unloading, x_poly_unloading),
                                      color='green', alpha=0.3, label="Plastic {}%".format(unloading_area_fraction))

                    # Inset (zoomed area)
                    zoom_region_start = x_intersection_point - 50
                    zoom_region_end = x_intersection_point + 1
                    y_max = y_intersection_point + 1
                    y_min = y_fit_elastic_unloading[
                        min(range(len(x_fit_elastic_unloading)),
                            key=lambda i: abs(x_fit_elastic_unloading[i] - zoom_region_start))]
                    rect = Rectangle((zoom_region_start, y_min),
                                     zoom_region_end - zoom_region_start, y_max - y_min,
                                     linewidth=1, edgecolor='r', facecolor='none')
                    plt.gca().add_patch(rect)

                    plt.xlabel("Displacement Into Surface / $nm$")
                    plt.ylabel("Load on Sample / $mN$")
                    plt.ylim(bottom=0)
                    plt.xlim(left=0)
                    plt.legend()

                    plt.title(self.plottitle.format(self.filename.split(".")[0], str(i), hardnessCSM, np.round(GPa, 2)))
                    ax = plt.gca()
                    axins = inset_axes(ax, width="40%", height="40%", loc=6)  # Adjust loc as needed

                    axins.fill_betweenx(y_poly_loading, x_poly_loading,
                                      np.interp(y_poly_loading, y_poly_unloading, x_poly_unloading), color='blue',
                                      alpha=0.3)

                    axins.fill_betweenx(y_fit_elastic_unloading, x_fit_elastic_unloading,
                                      np.interp(y_fit_elastic_unloading, y_poly_unloading, x_poly_unloading),
                                      color='green', alpha=0.3)

                    axins.plot(x_poly_loading, y_poly_loading, '-')
                    axins.plot(x_poly_unloading, y_poly_unloading, '-')
                    axins.plot(x_fit_elastic_unloading, y_fit_elastic_unloading, '-')
                    axins.scatter(df_loading_sample["Displacement Into Surface"], df_loading_sample["Load On Sample"],
                                  edgecolors='orange', facecolors='none', marker='o')
                    axins.scatter(df_unloading_sample["Displacement Into Surface"],
                                  df_unloading_sample["Load On Sample"],
                                  edgecolors='orange', facecolors='none', marker='o')
                    axins.tick_params(labelleft=False, labelbottom=False, left=False, right=False, top=False,
                                      bottom=False)
                    axins.set_xlim(zoom_region_start, zoom_region_end)  # Zoom in on x-axis
                    axins.set_ylim(y_min, y_max)  # Zoom in on y-axis

                    if self.export:
                        exportpath = os.path.join(
                            self.filename.split(".")[0],
                            self.plottitle.format(self.filename.split(".")[0], str(i), hardnessCSM,
                                                  np.round(GPa, 2)) + ".png",
                        )
                        Path(exportpath).parent.mkdir(parents=True, exist_ok=True)
                        plt.savefig(exportpath)
                    if not self.hidePlot:
                        plt.show()
            except:
                pass

        df_Results = pd.DataFrame(all_results)
        if self.export:
            df_Results.to_csv(os.path.join(self.filename.split(".")[0], "Results.csv"), index=False)

        return df_Results

    def Contact_area_from_coefficients(self, h, coeffs):
        """
        Calculate the contact area A(h) using the provided coefficients.

        Parameters:
        - h: Contact depth in meters (m).
        - coeffs: Coefficients [C0, C1, C2, C3].

        Returns:
        - A(h): Contact area in square meters (m²).
        """
        h = np.abs(h)  # Ensure non-negative depth
        # Each term assumes SI units for h and coeffs
        A = coeffs[0] * h ** 2 + coeffs[1] * h + coeffs[2] * h ** 0.5 + coeffs[3] * h ** 0.25
        return A

    def calculate_contact_area(self, S_N_per_m, Er_Pa):
        """
        Calculate the contact area Ap based on stiffness and reduced modulus.

        Parameters:
        - S_N_per_m: Contact stiffness in Newtons per meter (N/m).
        - Er_Pa: Reduced modulus in Pascals (Pa).

        Returns:
        - Ap: Contact area in square meters (m²).
        """
        # Ensure both inputs are in SI units
        Ap = ((S_N_per_m / (2 * Er_Pa)) ** 2) * np.pi
        return Ap

    def compute_reduced_modulus(self, Es, poissons_ratio_s=0.17, Ei=1140 * 1e9, poissons_ratio_i=0.07):
        """
        Compute the reduced modulus Er.

        Parameters:
        - Es: Elastic modulus of the sample in Pascals (Pa).
        - poissons_ratio_s: Poisson's ratio of the sample (unitless).
        - Ei: Elastic modulus of the indenter in Pascals (Pa).
        - poissons_ratio_i: Poisson's ratio of the indenter (unitless).

        Returns:
        - Er: Reduced modulus in Pascals (Pa).
        """
        # Elastic modulus and Poisson's ratios must all use consistent SI units
        Er = 1 / ((1 - poissons_ratio_s ** 2) / Es + (1 - poissons_ratio_i ** 2) / Ei)
        return Er

    def CalculateR_2(self, x_true, y_true, poly_coeffs):
        """
        Calculate the R² value for a polynomial fit.

        Parameters:
        - x_true: True x-values (independent variable).
        - y_true: True y-values (dependent variable).
        - poly_coeffs: Coefficients of the polynomial.

        Returns:
        - R²: Coefficient of determination (unitless).
        """
        y_pred = np.polyval(poly_coeffs, x_true)
        ss_res = np.sum((y_true - y_pred) ** 2)  # Residual sum of squares
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)  # Total sum of squares
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared

    def CalculateMAE(self, x_true, y_true, poly_coeffs):
        y_pred = np.polyval(poly_coeffs, x_true)
        mae = np.mean(np.abs(y_true - y_pred))
        return mae

    def CalculateMSE(self, x_true, y_true, poly_coeffs):
        y_pred = np.polyval(poly_coeffs, x_true)
        mse = np.mean((y_true - y_pred) ** 2)
        return mse

    def CalculateMAPE(self, x_true, y_true, poly_coeffs):
        y_pred = np.polyval(poly_coeffs, x_true)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        return mape

    def find_closest_intersection_point(self, coeffs1, coeffs2, coeffs3):
        """
        Find the closest intersection point of three polynomials.

        Parameters:
        - coeffs1: Coefficients of the first polynomial.
        - coeffs2: Coefficients of the second polynomial.
        - coeffs3: Coefficients of the third polynomial.

        Returns:
        - x_min_difference: x-value of the closest intersection in meters (m).
        - y_min_difference: y-value of the closest intersection in Newtons (N).
        """

        def difference_in_y(x):
            y1 = np.polyval(coeffs1, x)
            y2 = np.polyval(coeffs2, x)
            y3 = np.polyval(coeffs3, x)
            return abs(y1 - y2) + abs(y1 - y3) + abs(y2 - y3)

        # Use minimize_scalar, which does not require x0
        result = minimize_scalar(difference_in_y, bounds=(0, 2000), method='bounded')  # Adjust bounds for meters

        if result.success:
            x_min_difference = result.x
            y_min_difference = np.polyval(coeffs1, x_min_difference)
            return x_min_difference, y_min_difference
        else:
            return None, None

    def optimize_tip_coeffs(self, Hc, S, Er, initial_coeffs):
        """
        Optimize the last three tip coefficients (C1, C2, C3) while keeping C0 fixed.

        Parameters:
        - Hc: Contact depth in meters (m).
        - S: Contact stiffness in Newtons per meter (N/m).
        - Er: Reduced modulus in Pascals (Pa).
        - initial_coeffs: Initial guess for tip coefficients [C0, C1, C2, C3].

        Returns:
        - Full coefficients [C0, C1, C2, C3] with C0 fixed.
        """
        fixed_C0 = initial_coeffs[0]  # Fix the first coefficient (C0)

        def objective(coeffs):
            # Combine fixed C0 with the optimized coefficients
            full_coeffs = [fixed_C0, *coeffs]
            A_h = self.Contact_area_from_coefficients(Hc, full_coeffs)
            A_p = self.calculate_contact_area(S, Er)
            return abs(A_p - A_h)

        # Initial guess for the coefficients to optimize (C1, C2, C3)
        x0 = initial_coeffs[1:]

        # Optimize the last three coefficients
        result = minimize(objective, x0=x0, method='Nelder-Mead', options={'xatol': 1e-8, 'fatol': 1e-8})

        if result.success:
            return [fixed_C0, *result.x]
        else:
            return None
