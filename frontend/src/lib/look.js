import {
  AirVent, Battery, BatteryCharging, Blend, Camera, Cctv, ChefHat, Coffee, CookingPot, Fan, Flame,
  GlassWater, HardDrive, Headphones, Heater, Keyboard, Laptop, MemoryStick, Microwave, Monitor, Package,
  Plug, Printer, Projector, Refrigerator, Sandwich, Scissors, Shirt, Smartphone, Snowflake, Sparkles,
  Speaker, Tablet, Tv, Usb, Utensils, WashingMachine, Watch, Wind, Zap, Droplets, Computer, Soup,
} from 'lucide-react'

// Each category gets one soft colour, so lists are easier to scan. Green is
// kept for "lowest price" only, so no category uses it.
const CATEGORY_HUE = {
  Televisions: 'indigo',
  'Mobiles & Tablets': 'violet',
  Computers: 'sky',
  Wearables: 'pink',
  'Home Audio': 'pink',
  Accessories: 'slate',
  'Large Appliances': 'sky',
  'Air & Cooling': 'teal',
  'Kitchen Appliances': 'coral',
  'Other Kitchen & Home': 'amber',
  'Home Appliances': 'teal',
  'Personal Care': 'violet',
  'Power & Backup': 'amber',
  'Home Automation': 'indigo',
}

export const hueOf = (category) => CATEGORY_HUE[category] ?? 'slate'

const TYPE_ICON = {
  Television: Tv, 'Mobile Phone': Smartphone, Tablet, Laptop, 'Desktop Computer': Computer, Monitor, Printer, Projector,
  Refrigerator, 'Commercial Refrigerator': Refrigerator, 'Chest Freezer': Snowflake,
  'Washing Machine': WashingMachine, 'Washer Dryer': WashingMachine, 'Clothes Dryer': WashingMachine,
  'Air Conditioner': AirVent, 'Air Cooler': Wind, 'Ceiling Fan': Fan, 'Pedestal Fan': Fan, 'Table Fan': Fan, 'Wall Fan': Fan,
  'Microwave Oven': Microwave, 'Oven Toaster Grill': Microwave, 'Air Fryer': CookingPot, 'Rice Cooker': CookingPot,
  'Mixer Grinder': Blend, 'Wet Grinder': Blend, 'Blender & Juicer': Blend, 'Food Processor': Blend,
  Chimney: Wind, Hob: Flame, 'Gas Stove': Flame, 'Induction Cooker': Zap, 'Cooking Range': Flame,
  'Electric Kettle': Coffee, 'Sandwich Maker': Sandwich, 'Noodle Maker': Soup, 'Soda Maker': GlassWater,
  Dishwasher: Utensils, Cookware: ChefHat, 'Lunch Box': Package, 'Bottle & Flask': GlassWater, 'Other Kitchen & Home Item': Package,
  Iron: Shirt, 'Vacuum Cleaner': Sparkles, 'Water Heater': Heater, 'Water Purifier': Droplets, 'Water Dispenser': Droplets,
  Speaker, Soundbar: Speaker, 'Home Theater': Speaker, Earbuds: Headphones, Headphones,
  'Smart Watch': Watch, 'Security Camera': Cctv, 'Power Bank': BatteryCharging, 'Flash Drive': Usb,
  'Memory Card': MemoryStick, 'Hard Drive': HardDrive, 'Mouse & Keyboard': Keyboard,
  Inverter: Plug, Battery, 'Voltage Stabilizer': Zap,
  'Hair Dryer': Wind, 'Hair Straightener': Sparkles, 'Trimmer & Shaver': Scissors, Perfume: Sparkles,
}

const CATEGORY_ICON = {
  Televisions: Tv, 'Mobiles & Tablets': Smartphone, Computers: Laptop, Wearables: Watch, 'Home Audio': Speaker,
  Accessories: Headphones, 'Large Appliances': Refrigerator, 'Air & Cooling': AirVent, 'Kitchen Appliances': CookingPot,
  'Other Kitchen & Home': ChefHat, 'Home Appliances': Shirt, 'Personal Care': Scissors, 'Power & Backup': BatteryCharging,
  'Home Automation': Camera,
}

export const iconOf = (productType, category) => TYPE_ICON[productType] ?? CATEGORY_ICON[category] ?? Package

// Our own colours for telling the stores apart, not their brand colours.
const STORE_HUE = { myG: 'violet', Oxygen: 'sky', Pittappillil: 'amber', 'Nandilath G Mart': 'coral' }
export const storeHue = (name) => STORE_HUE[name] ?? 'slate'
