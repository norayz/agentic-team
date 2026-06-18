class MenuService {
  constructor(database) {
    this.db = database.db;
  }

  getAllMenuItems(callback) {
    this.db.all('SELECT * FROM menu_items ORDER BY name', [], (err, rows) => {
      if (err) {
        return callback(err, null);
      }
      callback(null, rows);
    });
  }
}

module.exports = MenuService;
