def serialize_tuple_keys(obj):
    ret ={}
    for key, value in obj.items():
        str_key = key[0] + "_" + key[1]
        str_value = [] 
        for item in value:
            str_value.append(item[0] + "_" + item[1])
        ret[str_key] = str_value
    return ret
