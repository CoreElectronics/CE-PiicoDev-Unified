

# General Guidelines
What | Why
--- | ---
Constants are to be defined outside the class in upper case with the pythonic leading underscore. | May conserve RAM because if there are multiple instances of the class, there is still only one instance of each constant.
If a method is accessing a read only value its name should have a prefix *read*.  If it is accessing a read/write value its name should have the prefix *set* or *get* | Consistency.

# Inclusive Language
I2C devices are either a *controller* or *target*.
