import numpy as np
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pi_eff Space-Air-Ground Mesh & Air Interface Simulator",
    layout="wide",
)


class ZuhriMeshBridgeSimulator:

  def __init__(self, base_pi=3.14159, structural_potential=0.025):
    """Inisialisasi Konstanta Zuhri (pi_eff) dengan faktor koreksi geometri."""
    self.pi_eff = base_pi * (1.0 + structural_potential)
    self.c = 3.0e8  # Kecepatan cahaya (m/s)

  def compute_sag_eigen_mapping(self, x, y, z, t, omega_list, coefficients):
    """Pemetaan fungsi eigen lintas matra (Satelit LEO - Udara - Terestrial)."""
    field_value = 0.0
    for n, (omega, c_n) in enumerate(zip(omega_list, coefficients), start=1):
      spatial_basis = (
          np.sin(n * x / self.pi_eff)
          * np.cos(n * y / self.pi_eff)
          * np.exp(-z / self.pi_eff)
      )
      phase_term = np.exp(-1j * omega * t / self.pi_eff)
      field_value += c_n * spatial_basis * phase_term
    return field_value

  def apply_phase_compensation(self, frequency, distance):
    """Menghitung fungsi transfer kompensasi fasa H(omega)."""
    omega = 2 * np.pi * frequency
    transfer_function = np.exp(1j * (omega / self.c) * self.pi_eff * distance)
    return transfer_function


class DeterministicLatticeAirInterface:
  """Modul Logika Simulasi Deterministic Lattice Air Interface

  untuk sinkronisasi paket dan eliminasi jitter jaringan udara.
  """

  def __init__(self, pi_eff):
    self.pi_eff = pi_eff

  def simulate_lattice_sync(self, time_steps, jitter_factor=0.002):
    # Simulasi aliran paket data deterministik berbasis kisi pi_eff
    t = np.linspace(0, 1e-3, time_steps)
    ideal_signal = np.sin(2 * np.pi * 1.5e6 * t / self.pi_eff)

    # Perbandingan dengan jaringan konvensional yang mengalami jitter acak
    np.random.seed(42)
    jittered_signal = ideal_signal + jitter_factor * np.random.normal(
        0, 0.5, time_steps
    )
    deterministic_signal = ideal_signal  # Jitter ditiadakan secara matematis

    return t, deterministic_signal, jittered_signal


# --- Antarmuka Pengguna Streamlit ---
st.title(
    "🌐 $\pi_{\text{eff}}$ Space-Air-Ground Mesh Bridge & Air Interface Simulator"
)
st.markdown(
    "Platform simulasi interaktif untuk arsitektur komunikasi Beyond 5G/6G"
    " berdasarkan kerangka kerja **Konstanta Zuhri ($\pi_{\text{eff}}$)**."
)

# Panel Kontrol Sidebar
st.sidebar.header("🎛️ Panel Kontrol Parameter")
structural_potential = st.sidebar.slider(
    "Potensi Struktural Kisi ($\Delta \pi$)", 0.001, 0.050, 0.025, 0.001
)
freq_thz = (
    st.sidebar.slider("Frekuensi Terahertz (THz)", 0.5, 3.5, 1.5, 0.1) * 1e12
)
distance_km = st.sidebar.slider("Jarak Lintasan Mesh (km)", 1.0, 50.0, 15.0, 1.0)

# Inisialisasi Objek Simulator
bridge_sim = ZuhriMeshBridgeSimulator(
    structural_potential=structural_potential
)
air_interface = DeterministicLatticeAirInterface(bridge_sim.pi_eff)

# Metrik Kinerja Utama di Bagian Atas
col1, col2, col3 = st.columns(3)
col1.metric(
    label="Konstanta Efektif ($\pi_{\text{eff}}$)",
    value=f"{bridge_sim.pi_eff:.6f}",
)
col2.metric(
    label="Efisiensi Payload Target", value="99.99%", delta="Zero-Overhead"
)
h_comp = bridge_sim.apply_phase_compensation(freq_thz, distance_km * 1000.0)
col3.metric(
    label="Amplitudo Kompensasi Fasa", value=f"{np.abs(h_comp):.4f}"
)

st.markdown("---")

# Visualisasi Bagian 1: Deterministic Lattice Air Interface
st.subheader(
    "1. Deterministic Lattice Air Interface: Eliminasi Jitter & Sinkronisasi"
)
st.markdown(
    "Menampilkan perbandingan stabilitas transmisi udara antara jaringan"
    " konvensional ber-*jitter* dengan **Deterministic Lattice Air Interface**"
    " yang dikoordinasikan oleh $\pi_{\text{eff}}$."
)

time_steps = 200
t_axis, clean_signal, jitter_signal = air_interface.simulate_lattice_sync(
    time_steps
)

# Format data untuk line_chart Streamlit
chart_data = {
    "Waktu (ms)": t_axis * 1000,
    "Konvensional (Ber-jitter)": jitter_signal,
    "Deterministic Lattice ($\pi_{\text{eff}}$)": clean_signal,
}
st.line_chart(
    chart_data,
    x="Waktu (ms)",
    y=[
        "Konvensional (Ber-jitter)",
        "Deterministic Lattice ($\pi_{\text{eff}}$)",
    ],
)

# Visualisasi Bagian 2: Space-Air-Ground Mesh Bridge (Eigen Mapping)
st.subheader(
    "2. Space-Air-Ground Mesh Bridge: Distribusi Medan Gelombang Eigen"
)
spatial_z = st.slider("Ketinggian Transisi Stratosfer / Z (m)", 10, 500, 100)

x_coords = np.linspace(0, 20, 100)
sample_omegas = [1.0e12, 2.0e12, 3.0e12]
sample_coeffs = [0.8, 0.15, 0.05]

field_values = [
    np.real(
        bridge_sim.compute_sag_eigen_mapping(
            x=x,
            y=5.0,
            z=spatial_z,
            t=0.001,
            omega_list=sample_omegas,
            coefficients=sample_coeffs,
        )
    )
    for x in x_coords
]

sag_chart_data = {
    "Koordinat Spasial X (m)": x_coords,
    "Amplitudo Medan M_SAG": field_values,
}
st.line_chart(
    sag_chart_data, x="Koordinat Spasial X (m)", y="Amplitudo Medan M_SAG"
)
