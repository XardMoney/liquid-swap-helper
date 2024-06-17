from dataclasses import dataclass, fields
import pandas as pd


@dataclass
class ExcelAccountData:
    name: str
    private_key: str
    proxy: str | None
    cex_address: str

    @classmethod
    def from_dataframe_row(cls, row):
        kwargs = {}
        for f in fields(cls):
            if f.name in row:
                value = row[f.name]
                if pd.isna(value):
                    if type(None) not in getattr(f.type, '__args__', ()):
                        raise ValueError(f"The field '{f.name}' is required but missing in row: {row}")
                    kwargs[f.name] = None
                else:
                    kwargs[f.name] = value
            else:
                if type(None) not in getattr(f.type, '__args__', ()):
                    raise ValueError(f"The field '{f.name}' is required but missing in row: {row}")
                kwargs[f.name] = None
        return cls(**kwargs)
