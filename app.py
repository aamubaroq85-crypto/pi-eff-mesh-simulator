import numpy as np
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pi_eff Mesh & Local Wireless Simulator", layout="wide"
)


class ZuhriMeshBridgeSimulator:

  def __init__(self, base_pi=3.14159, structural_potential=0.025):
    self.base_pi = base_pi
    self.structural_potential = structural_potential
    self.pi_eff = self.calculate_effective_pi(0.001, 1.5e12, 0.0)
    self.c = 3.0e8  # Kecepatan cahaya (m/s)

  def calculate_effective_pi(
      self, contour_integral_value, wavelength_thz, weather_attenuation=0.0
  ):
    correction_factor = (contour_integral_value / wavelength_thz) - (
        weather_attenuation * 0.05
    )
    self.pi_eff = self.base_pi * (
        1.0 + self.structural_potential + correction_factor
    )
    return self.pi_eff

  def compute_sag_eigen_mapping(
      self, x, y, z, t, omega_list, coefficients, weather_attenuation=0.0
  ):
    field_value = 0.0
    attenuation_factor = np.exp(-weather_attenuation * z / 1000.0)
    for n, (omega, c_n) in enumerate(zip(omega_list, coefficients), start=1):
      spatial_basis = (
          np.sin(n * x / self.pi_eff)
          * np.cos(n * y / self.pi_eff)
          * np.exp(-z / self.pi_eff)
      )
      phase_term = np.exp(-1j * omega * t / self.pi_eff)
      field_value += c_n * spatial_basis * phase_term * attenuation_factor
    return field_value

  def apply_phase_compensation(self, frequency, distance):
    omega = 2 * np.pi * frequency
    transfer_function = np.exp(1j * (omega / self.c) * self.pi_eff * distance)
    return transfer_function


class DeterministicLatticeAirInterface:

  def __init__(self, pi_eff):
    self.pi_eff = pi_eff

  def simulate_lattice_sync(self, time_steps, weather_attenuation=0.0):
    t = np.linspace(0, 1e-3, time_steps)
    ideal_signal = np.sin(2 * np.pi * 1.5e6 * t / self.pi_eff)

    np.random.seed(42)
    jitter_factor = 0.002 + (weather_attenuation * 0.01)
    jittered_signal = (
        ideal_signal
        + jitter_factor * np.random.normal(0, 0.5, time_steps)
        - (weather_attenuation * 0.1)
    )
    deterministic_signal = ideal_signal
    return t, deterministic_signal, jittered_signal


# --- Antarmuka Pengguna Streamlit ---
st.title(
    "🌐 Simulator Jaringan Mandiri & $\pi_{\text{eff}}$ Space-Air-Ground Bridge"
)
st.markdown(
    "Platform simulasi perangkat lunak untuk merancang **Jaringan Mesh Lokal"
    " Tanpa Kuota Seluler** berbasis kerangka kerja **Konstanta Zuhri"
    " ($\pi_{\text{eff}}$)**."
)

# Panel Kontrol Sidebar
st.sidebar.header("🎛️ Parameter Fisika & Gelombang")
structural_potential = st.sidebar.slider(
    "Potensi Struktural Kisi ($\Delta \pi$)", 0.001, 0.050, 0.025, 0.001
)
freq_thz = (
    st.sidebar.slider("Frekuensi Pembawa (THz / GHz)", 0.5, 3.5, 1.5, 0.1) * 1e12
)
distance_km = st.sidebar.slider("Jarak Jangkauan Antar-Node (km)", 1.0, 50.0, 15.0, 1.0)

st.sidebar.markdown("---")
st.sidebar.header("🌧️ Modul Cuaca & Lingkungan")
preset_option = st.sidebar.selectbox(
    "Pilih Skenario Preset:",
    [
        "Kustom (Manual)",
        "☀️ Cerah Normal (Att: 0.0)",
        "🌧️ Badai Hujan Tropis (Att: 0.5)",
        "🌪️ Turbulensi Ekstrem (Att: 1.0)",
    ],
)

if preset_option == "☀️ Cerah Normal (Att: 0.0)":
  default_att = 0.0
elif preset_option == "🌧️ Badai Hujan Tropis (Att: 0.5)":
  default_att = 0.5
elif preset_option == "🌪️ Turbulensi Ekstrem (Att: 1.0)":
  default_att = 1.0
else:
  default_att = 0.0

weather_attenuation = st.sidebar.slider(
    "Indeks Redaman Lingkungan", 0.0, 1.0, float(default_att), 0.05
)

# Inisialisasi Objek Simulator
bridge_sim = ZuhriMeshBridgeSimulator(
    structural_potential=structural_potential
)
current_pi_eff = bridge_sim.calculate_effective_pi(
    0.002, freq_thz, weather_attenuation
)
air_interface = DeterministicLatticeAirInterface(current_pi_eff)

# --- Menu Navigasi / Tab Simulasi Perangkat Lunak ---
tab1, tab2, tab3 = st.tabs([
    "📊 Metrik & Komparasi Latensi",
    "📡 Simulasi Transmisi Paket Tanpa Kuota",
    "🗺️ Arsitektur Jaringan Mesh Lokal",
])

with tab1:
  st.subheader("📊 Metrik Kinerja Jaringan & Kalkulator Waktu Nyata")
  col1, col2, col3, col4 = st.columns(4)

  col1.metric(
      label="Konstanta Efektif ($\pi_{\text{eff}}$)",
      value=f"{current_pi_eff:.6f}",
  )

  conv_latency_ms = distance_km * 3.33 + (weather_attenuation * 25.0)
  mesh_latency_ms = 0.0000

  col2.metric(
      label="Jaringan Seluler Konvensional",
      value=f"{conv_latency_ms:.2f} ms",
      delta="Butuh Kuota / Fluktuatif",
      delta_color="inverse",
  )
  col3.metric(
      label="$\pi_{\text{eff}}$ Mesh Mandiri",
      value=f"{mesh_latency_ms:.4f} ms",
      delta="Zero-Loss / Gratis",
  )

  h_comp = bridge_sim.apply_phase_compensation(freq_thz, distance_km * 1000.0)
  col4.metric(
      label="Amplitudo Kompensasi Fasa", value=f"{np.abs(h_comp):.4f}"
  )

  st.markdown("##### 📈 Grafik Komparasi Latensi Langsung")
  latency_comparison_df = pd.DataFrame({
      "Tipe Jaringan": [
          "Seluler Konvensional (Berbayar/Kuota)",
          "Mesh Mandiri ($\pi_{\text{eff}}$)",
      ],
      "Latensi (ms)": [conv_latency_ms, mesh_latency_ms],
  })
  st.bar_chart(latency_comparison_df, x="Tipe Jaringan", y="Latensi (ms)")

with tab2:
  st.subheader(
      "📡 Modul Simulasi Transmisi Paket Data Lokal (Tanpa Kuota Seluler)"
  )
  st.markdown(
      "Simulasi pengiriman paket data teks/multimedia antar perangkat dalam"
      " jaringan lokal berbasis koreksi fasa deterministik."
  )

  # Parameter Simulasi Paket
  packet_size_kb = st.slider(
      "Ukuran Paket Data (KB)", 10, 1024, 256, 16
  )
  transmission_power_dbm = st.slider(
      "Daya Pancar Radio Lokal (dBm)", 10, 30, 20, 1
  )

  # Perhitungan teoretis throughput dan packet loss lokal
  free_space_loss = 20 * np.log10(distance_km * 1000) + 20 * np.log10(
      freq_thz / 1e9
  ) + 92.45
  effective_signal_strength = (
      transmission_power_dbm - free_space_loss - (weather_attenuation * 15)
  )
  packet_success_rate = max(
      0.0,
      min(
          100.0,
          100.0
          - (weather_attenuation * 10)
          + (np.abs(current_pi_eff - 3.14159) * 5),
      ),
  )

  col_p1, col_p2, col_p3 = st.columns(3)
  col_p1.metric(
      label="Kekuatan Sinyal Terima (RSSI)",
      value=f"{effective_signal_strength:.2f} dBm",
  )
  col_p2.metric(
      label="Tingkat Keberhasilan Paket",
      value=f"{packet_success_rate:.2f}%",
      delta="Stabil",
  )
  col_p3.metric(
      label="Estimasi Throughput Lokal",
      value=f"{100 / (1 + weather_attenuation):.1f} Mbps",
  )

  # Visualisasi Gelombang Sinkronisasi
  time_steps = 200
  t_axis, clean_signal, jitter_signal = air_interface.simulate_lattice_sync(
      time_steps, weather_attenuation
  )
  chart_data = {
      "Waktu (ms)": t_axis * 1000,
      "Derau / Interferensi Lingkungan": jitter_signal,
      "Sinyal Mesh Deterministik ($\pi_{\text{eff}}$)": clean_signal,
  }
  st.line_chart(
      chart_data,
      x="Waktu (ms)",
      y=[
          "Derau / Interferensi Lingkungan",
          "Sinyal Mesh Deterministik ($\pi_{\text{eff}}$)",
      ],
  )

with tab3:
  st.subheader("🗺️ Skema Arsitektur Jaringan Mesh Komunitas Lokal")
  col_arch1, col_arch2, col_arch3 = st.columns(3)
  col_arch1.info(
      "🛰️ **Node Backbone / Satelit**\n\nTitik kumpul sinyal langit / HAP"
      " komunal."
  )
  col_arch2.warning(
      "✈️ **Node Relay Udara/Menara**\n\nPenguat sinyal atap rumah / tiang"
      " desa."
  )
  col_arch3.success(
      "📱 **Node Pengguna Akhir**\n\nHP / Laptop warga terhubung tanpa kuota."
  )

  st.markdown("---")
  st.subheader("📥 Ekspor Log Simulasi Perangkat Lunak")
  export_df = pd.DataFrame({
      "Jarak_km": [distance_km],
      "Frekuensi_THz": [freq_thz / 1e12],
      "Pi_Eff": [current_pi_eff],
      "RSSI_dBm": [effective_signal_strength],
      "Success_Rate_Percent": [packet_success_rate],
  })
  csv_data = export_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Unduh Log Simulasi Jaringan (.CSV)",
      data=csv_data,
      file_name="local_mesh_simulation_log.csv",
      mime="text/csv",
  )
