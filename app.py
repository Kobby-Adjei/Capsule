from flask import Flask,request
import uuid
app = Flask(__name__)
CAPSULES = []

@app.post("/capsules")
def create_capsule():
    data = request.get_json()
    cid = "cap_" + uuid.uuid4().hex[:6]  #give each capsule an id
    data["id"] = cid
    CAPSULES.append(data)
    return data

   
@app.get("/capsules")
def get_capsules():
    return{"capsules":CAPSULES}
  
@app.get("/health")
def health():
    return {"ok":True}
app.run(port=5001)

