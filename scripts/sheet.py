import sys
from PIL import Image
out=sys.argv[1]; files=sys.argv[2:]
ims=[Image.open(f).convert('RGB') for f in files]
h=640; ims=[i.resize((int(i.width*h/i.height),h)) for i in ims]
cols=4; rows=(len(ims)+cols-1)//cols
W=max(i.width for i in ims)
sheet=Image.new('RGB',(W*cols,h*rows),(20,20,20))
for k,i in enumerate(ims): sheet.paste(i,((k%cols)*W,(k//cols)*h))
sheet.save(out,quality=85)
