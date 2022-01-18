import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pyroomacoustics as pra
import soundfile as sf
from flask import Flask, render_template, request

app = Flask(__name__)

# バックエンドを指定
matplotlib.use("Agg")


instruments = ["Vo.", "Ba.", "Dr.", "Oth."]
is_exist = {
    "Vo.": True,
    "Ba.": True,
    "Dr.": True,
    "Oth.": True,
}

room_size = [3.6, 4.5, 2.7]
fw = 0.14  # face width
locations = {
    "Vo.": [1.6, 2.25, 1.7],
    "Ba.": [2.1, 3.5, 1.0],
    "Dr.": [2.6, 2.25, 1.0],
    "Oth.": [2.1, 1.0, 1.0],
    "Mic.": [[0.5, 2.25 + fw / 2, 1.7], [0.5, 2.25 - fw / 2, 1.7]],
}

vo_sig, fs = sf.read("sources/vocals.wav")
dr_sig, _ = sf.read("sources/drums.wav")
ba_sig, _ = sf.read("sources/bass.wav")
oth_sig, _ = sf.read("sources/other.wav")

signals = {
    "Vo.": vo_sig,
    "Ba.": ba_sig,
    "Dr.": dr_sig,
    "Oth.": oth_sig,
}


def generate_premix(room_size, is_exist, locations, signals, rt60, fs):
    # generate room
    e_absorption, max_order = pra.inverse_sabine(rt60, room_size)
    room = pra.ShoeBox(
        room_size, fs=fs, materials=pra.Material(e_absorption), max_order=max_order
    )

    # set mic
    locations_mic = np.c_[
        locations["Mic."][0],  # L
        locations["Mic."][1],  # R
    ]
    room.add_microphone_array(locations_mic)

    # add multiple sources
    for inst in instruments:
        if is_exist[inst]:
            sig_len, n_channel = signals[inst].shape
            room.add_source(np.array(locations[inst]), signal=signals[inst][:, 0])

    room.simulate()
    recording = room.mic_array.signals

    return recording


def generate_recording():

    rt60 = 0.15

    # 音声の書き出し
    recording = np.array(
        generate_premix(room_size, is_exist, locations, signals, rt60, fs)
    )
    sf.write("./static/spatial-mix.wav", recording.T, fs)


def plot_room():
    plt.figure(figsize=(16, 8))
    for inst in instruments:
        if is_exist[inst]:
            plt.scatter(locations[inst][0], locations[inst][1], s=100, label=inst)

    # Left
    plt.scatter(locations["Mic."][0][0], locations["Mic."][0][1], s=50, color="black")
    # Right
    plt.scatter(
        locations["Mic."][1][0],
        locations["Mic."][1][1],
        s=50,
        color="black",
        label="Mic.",
    )

    plt.xlim(0.0, 3.6)
    plt.ylim(0.0, 4.5)
    plt.legend(fontsize=15)
    plt.savefig("./static/arrangement.png")


# main
@app.route("/", methods=["GET", "POST"])
def form():
    # ２回目以降データが送られてきた時の処理です
    if request.method == "POST":

        instrument = request.form["instrument"]
        x = int(request.form["x"])
        y = int(request.form["y"])
        # is_exist = request.form["is_exist"]

        generate_recording()
        plot_room()
        return render_template("index.html", instruments=instruments)

    # １回目のデータが何も送られてこなかった時の処理です。
    else:

        generate_recording()
        plot_room()
        return render_template("index.html", instruments=instruments)


# アプリケーションを動かすためのおまじない
if __name__ == "__main__":
    app.run(port=8000, debug=True)
