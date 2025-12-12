import React from 'react';

// Admin Imports

// Icon Imports
import {
  MdHome,
  MdOutlineShoppingCart,
  MdBarChart,
  MdPerson,
  MdLock,
  MdVideoLibrary,
  MdSearch,
  MdHistory,
  MdAutorenew,
} from 'react-icons/md';

const routes = [
  {
    name: 'Main Dashboard',
    layout: '/admin',
    path: 'default',
    icon: <MdHome className="h-6 w-6" />,
  },
  {
    name: 'My Videos',
    layout: '/admin',
    path: 'my-videos',
    icon: <MdVideoLibrary className="h-6 w-6" />,
  },
  {
    name: 'Browse Videos',
    layout: '/admin',
    path: 'browse',
    icon: <MdSearch className="h-6 w-6" />,
  },
  {
    name: 'Scan History',
    layout: '/admin',
    path: 'history',
    icon: <MdHistory className="h-6 w-6" />,
  },
  {
    name: 'Model Management',
    layout: '/admin',
    path: 'model',
    icon: <MdAutorenew className="h-6 w-6" />,
  },
  // {
  //   name: 'NFT Marketplace',
  //   layout: '/admin',
  //   path: 'nft-marketplace',
  //   icon: <MdOutlineShoppingCart className="h-6 w-6" />,

  //   secondary: true,
  // },
  // {
  //   name: 'Data Tables',
  //   layout: '/admin',
  //   icon: <MdBarChart className="h-6 w-6" />,
  //   path: 'data-tables',
  // },
  // {
  //   name: 'Profile',
  //   layout: '/admin',
  //   path: 'profile',
  //   icon: <MdPerson className="h-6 w-6" />,
  // },
  // {
  //   name: 'Sign In',
  //   layout: '/auth',
  //   path: 'sign-in',
  //   icon: <MdLock className="h-6 w-6" />,
  // },
  // {
  //   name: 'RTL Admin',
  //   layout: '/rtl',
  //   path: 'rtl-default',
  //   icon: <MdHome className="h-6 w-6" />,
  // },
];
export default routes;
