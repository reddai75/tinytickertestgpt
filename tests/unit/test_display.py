import os
from io import BytesIO
from pathlib import Path
from unittest import TestCase

import matplotlib.pyplot as plt
import pandas as pd
import pytest
from PIL import Image

from tinyticker.config import TinytickerConfig
from tinyticker.display import Display
from tinyticker.waveshare_lib._base import EPDBase
from tinyticker.waveshare_lib.models import MODELS, EPDModel

# if set to True, the reference plots will be updated
UPDATE_REF_PLOTS = os.environ.get("TINYTICKER_UPDATE_REF_PLOTS", False)


class EPDMock(EPDBase):
    def __init__(self) -> None:
        self.is_init = False
        self.width = 122
        self.height = 250

    def init(self) -> None:
        self.is_init = True

    def getbuffer(self, _: Image.Image) -> bytearray:
        return bytearray()

    def display(self, _: bytearray) -> None:
        pass

    def Clear(self) -> None:
        pass

    def sleep(self) -> None:
        pass


MODELS["mock"] = EPDModel(
    name="mock",
    class_=EPDMock,
    desc="A Mock display for testing",
)


class TestDisplay(TestCase):
    @classmethod
    def setUp(cls):
        cls.display = Display("mock")
        cls.display.epd
        cls.data_dir = Path(__file__).parents[1] / "data"
        cls.config_path = cls.data_dir / "config.json"
        cls.historical: pd.DataFrame = pd.read_pickle(
            cls.data_dir / "crypto_historical.pkl"
        )
        cls.crypto_historical_plot_file = cls.data_dir / "crypto_historical_plot.png"
        cls.crypto_historical_plot_volume_file = (
            cls.data_dir / "crypto_historical_plot_volume.png"
        )
        cls.text_plot_file = cls.data_dir / "text_plot.png"

    def test_init(self):
        with pytest.raises(KeyError):
            Display("Some model which does not exist")
        assert self.display.epd.is_init  # type: ignore

    def test_from_tt_config(self):
        tt_config = TinytickerConfig.from_file(self.config_path)
        tt_config.epd_model = "mock"
        display = Display.from_tinyticker_config(tt_config)
        assert display.flip == tt_config.flip

    def _check_fig_ax(self, fig, ax):
        assert (
            fig.get_size_inches() * fig.dpi
            == (
                self.display.epd.height,
                self.display.epd.width,
            )
        ).all()
        assert ax.margins() == (0, 0)
        assert ax.axison == False

    def _same_img(self, fig: plt.Figure, reference: Path) -> bool:
        """Helper function to compare the generated plot with the reference plot."""
        buf = BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return reference.open("rb").read() == buf.read()

    def test_plot(self):
        fig, ax = self.display.plot(self.historical, None)
        if UPDATE_REF_PLOTS:
            fig.savefig(self.crypto_historical_plot_file, format="png")
        self._check_fig_ax(fig, ax)
        assert self._same_img(fig, self.crypto_historical_plot_file)

    def test_plot_with_volume(self):
        fig, ax = self.display.plot(self.historical, None, volume=True)
        if UPDATE_REF_PLOTS:
            fig.savefig(self.crypto_historical_plot_volume_file, format="png")
        self._check_fig_ax(fig, ax)
        assert self._same_img(fig, self.crypto_historical_plot_volume_file)

    def test_text(self):
        text = "Some text"
        fig, ax = self.display.text(text)
        if UPDATE_REF_PLOTS:
            fig.savefig(self.text_plot_file, format="png")
        self._check_fig_ax(fig, ax)
        assert ax.texts[0]._text == text
        assert self._same_img(fig, self.text_plot_file)
