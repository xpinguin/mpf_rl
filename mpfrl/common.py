from numpy import *
from numpy import abs # override built-in 'abs()'
from numpy import max
from numpy import min

# ignore numpy underflow and overflow errors
#seterr(divide = "raise")
#seterr(invalid = "raise")

seterr(divide = "warn")
seterr(invalid = "warn")

seterr(under = "ignore")
seterr(over = "ignore")
# ---

# Now is set to 4byte float in order to keep memory
FLOAT_DTYPE = float32

# for some close-to-zero calculations
EPS = finfo(FLOAT_DTYPE).eps
F_MAX = finfo(FLOAT_DTYPE).max
F_MIN = finfo(FLOAT_DTYPE).min
