from app.interfaces.gui import gui as gui

try:

  gui().main()

except KeyboardInterrupt:

  gui().abort()