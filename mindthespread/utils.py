import importlib
import pandas

def get_class(cls: str):
    if isinstance(cls, str):
        module_name, cls = cls.rsplit('.', 1)
        module = importlib.import_module(module_name)
        cls = getattr(module, cls)

    return cls

def init_obj(cls: str, params=None):
    if params is None:
        params = {}
    cls = get_class(cls)
    instance = cls(**params)
    return instance


def align_indexes(df1: pandas.DataFrame, df2: pandas.DataFrame):
    index = df1.index.intersection(df2.index)
    df1_ = df1.loc[index]
    df2_ = df2.loc[index]
    return df1_, df2_


