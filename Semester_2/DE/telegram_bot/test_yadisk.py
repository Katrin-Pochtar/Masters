import yadisk

# Initialize the client with your token
y = yadisk.YaDisk(token="y0__xDaoO2kqveAAhigkzcg3unI7xLU6bexyLmAbp5RAYX8CN1Z3dn8mw")

# Check if we're authorized
if y.check_token():
    print("Token is valid")
    # Try to get disk info
    print("Disk info:", y.get_disk_info())
else:
    print("Token is not valid") 