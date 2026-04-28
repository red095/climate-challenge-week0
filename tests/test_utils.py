import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from app.utils import (
    extract_google_drive_file_id,
    extreme_heat_days,
    google_drive_download_url,
    load_country_data,
    normalize_csv_source,
    vulnerability_summary,
)


class GoogleDriveSourceTests(unittest.TestCase):
    def test_extracts_file_id_from_share_url(self):
        url = 'https://drive.google.com/file/d/abc123XYZ/view?usp=sharing'

        self.assertEqual(extract_google_drive_file_id(url), 'abc123XYZ')

    def test_normalizes_drive_share_url_to_download_url(self):
        url = 'https://drive.google.com/file/d/abc123XYZ/view?usp=sharing'

        self.assertEqual(
            normalize_csv_source(url),
            google_drive_download_url('abc123XYZ'),
        )

    def test_plain_drive_file_id_download_url(self):
        self.assertEqual(
            google_drive_download_url('abc123XYZ'),
            'https://drive.google.com/uc?export=download&id=abc123XYZ',
        )


class ClimateSummaryTests(unittest.TestCase):
    def test_load_country_data_accepts_year_and_doy_schema(self):
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / 'ethiopia_raw.csv'
            source.write_text(
                'YEAR,DOY,T2M,T2M_MAX,T2M_MIN,T2M_RANGE,PRECTOTCORR,'
                'RH2M,WS2M,WS2M_MAX,PS,QV2M\n'
                '2020,2,20,25,15,10,0,50,2,4,90,8\n'
            )
            df = load_country_data(
                'Ethiopia',
                data_dir='/tmp/no-local-climate-data',
                remote_sources={'Ethiopia': str(source)}
            )

        self.assertEqual(df.loc[0, 'Country'], 'Ethiopia')
        self.assertEqual(df.loc[0, 'Year'], 2020)
        self.assertEqual(df.loc[0, 'Month'], 1)
        self.assertEqual(str(df.loc[0, 'Date'].date()), '2020-01-02')

    def test_extreme_heat_days_includes_zero_years(self):
        df = pd.DataFrame({
            'Country': ['A', 'A', 'B', 'B'],
            'Year': [2020, 2020, 2020, 2021],
            'T2M_MAX': [34.0, 36.0, 30.0, 31.0],
        })

        result = extreme_heat_days(df)

        expected = pd.DataFrame({
            'Country': ['A', 'B', 'B'],
            'Year': [2020, 2020, 2021],
            'Extreme_Heat_Days': [1, 0, 0],
        })
        pd.testing.assert_frame_equal(result, expected)

    def test_vulnerability_rank_uses_lowest_score_as_highest_risk(self):
        df = pd.DataFrame({
            'Country': ['A', 'A', 'B', 'B'],
            'T2M': [30.0, 32.0, 20.0, 21.0],
            'PRECTOTCORR': [0.0, 10.0, 1.0, 1.1],
            'T2M_MAX': [40.0, 41.0, 25.0, 26.0],
        })

        result = vulnerability_summary(df)

        self.assertEqual(result.iloc[0]['Country'], 'A')
        self.assertEqual(result.iloc[0]['Rank'], 1)


if __name__ == '__main__':
    unittest.main()
