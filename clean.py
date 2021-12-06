import pickle
import pandas as pd
import re

cols = [
 'id',
 'artist',
 'painting',
 'paint_year',
 'sell_price',
 'est_min',
 'est_max',
 'sell_date',
 'seller',
 'link',
 'dimensions']

ds = [pickle.load(open("a_z_fin.pkl", "rb")),
 pickle.load(open("a_z_fin2.pkl", "rb"))]
fnames = ["a_z_fin.pkl", "a_z_fin2.pkl"]

unknown = 0
cur = 0

df = pd.DataFrame()
i = 0
for d, fname in zip(ds, fnames):
    arr = []
    print(fname)
    for k in d.keys():
        for row in d[k]:
            tmp = [i]
            tmp.append(k)
            tmp.append(row[0]) # painting name
            # parse year
            tmp.append(row[1])

            # parse sell-price
            if 'not communicated' == row[2] or '-sold-' == row[2] or "SOLD" == row[2]:
                unknown += 1
                tmp.append(None)
            elif "-not sold-" == row[2] or row[2] == 'withdrawn':
                tmp.append(0)
            elif 'Event coming soon' == row[2] or 'awaiting result' == row[2] or 'Event in progress' == row[2] or ""==row[2]:
                cur += 1
                continue
            # otherwise, parse scraped price
            else:
                tmp.append(int("".join(re.findall("[0-9]", row[2].split("\xa0")[0]))))
            # min and max price
            mn, mx = row[3].split(" - ")
            if mn == "n/a":
                tmp.append(None)
            else:
                tmp.append(int("".join(re.findall("[0-9]", mn))))
            if mx == "n/a":
                tmp.append(None)
            else:
                tmp.append(int("".join(re.findall("[0-9]", mx))))
            # selldate
            tmp.append(row[4])
            tmp.append(row[5])
            tmp.append(row[6])
            tmp.append(row[7])
            arr.append(tmp)
            i += 1
    df = df.append(pd.DataFrame(arr, columns=cols))
df = df.set_index('id')
print(f"{unknown} unknown, {cur} in progress and removed")
print(f"{len(df)} entries")
pickle.dump(df, open("df.pkl", "wb"))
