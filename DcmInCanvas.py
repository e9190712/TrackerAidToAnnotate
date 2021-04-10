import SimpleITK as sitk
from tkinter import *
from PIL import ImageTk, Image
from to_xml import CreateAnno
import cv2
import time
import tool
class ScrolledCanvas(Frame):
    def __init__(self, master, **kwargs):
        Frame.__init__(self, master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canv = Canvas(self, bd=0, highlightthickness=0)

        self.hScroll = Scrollbar(self, orient='horizontal',
                                 command=self.canv.xview)
        self.hScroll.grid(row=1, column=0, sticky='we')
        self.vScroll = Scrollbar(self, orient='vertical',
                                 command=self.canv.yview)
        self.vScroll.grid(row=0, column=1, sticky='ns')
        self.canv.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        self.canv.configure(xscrollcommand=self.hScroll.set,
                            yscrollcommand=self.vScroll.set)

class View(Tk):
    def __init__(self, dcm_path):
        Tk.__init__(self)
        self.dcm_path = dcm_path
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main = ScrolledCanvas(self)
        self.main.grid(row=0, column=0, sticky='nsew')
        self.c = self.main.canv
        # We will make the title of our app as Image Viewer
        self.List_images = [ImageTk.PhotoImage(image=Image.fromarray(im)) for im in
                            sitk.GetArrayFromImage(sitk.ReadImage(dcm_path))]
        self.show_images = [im for im in sitk.GetArrayFromImage(sitk.ReadImage(dcm_path))]
        self.wheel_num = 0
        self.start_frame = 0
        self.end_frame = len(self.List_images)
        self.boxes = []
        self.init_once = False
        self.c.bind('<ButtonPress-1>', self.on_mouse_down)
        self.c.bind('<B1-Motion>', self.on_mouse_drag)
        self.c.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.c.bind('<Button-3>', self.on_right_click)
    def save_data(self, count, img, view_img, bboxes):
        for (c, im, vimg, boxes) in zip(count, img, view_img, bboxes):
            cv2.imwrite(tool.make_path('label_output/img_3')+'/'+self.dcm_path.split('\\')[1].split('.')[0]+'_'+str(c)+'.png',im)
            cv2.imwrite(tool.make_path('label_output/view_img_3') + '/' + self.dcm_path.split('\\')[1].split('.')[0] + '_' + str(c) + '.png', vimg)
            xml_anno = CreateAnno()
            xml_anno.add_filename(self.dcm_path.split('\\')[1].split('.')[0] + '_' + str(c) + '.png')  # 檔名
            xml_anno.add_pic_size(width_text_str=str(im.shape[1]), height_text_str=str(im.shape[0]),
                                  depth_text_str=str(3))
            for bbox in boxes:
                xml_anno.add_object(name_text_str=str('sten_up50'),
                                    xmin_text_str=str(int(bbox[0])),
                                    ymin_text_str=str(int(bbox[1])),
                                    xmax_text_str=str(int(bbox[0] + bbox[2])),
                                    ymax_text_str=str(int(bbox[1] + bbox[3])))
            xml_anno.save_doc(tool.make_path('label_output/xml_3') + '/' + self.dcm_path.split('\\')[1].split('.')[0] + '_' + str(c) + '.xml')
        self.save_flag.destroy()
        self.Open()
    def start_tacker(self, im_array, start_frame, end_frame, boxes):
        tracker = cv2.MultiTracker_create()
        save_count=[]
        save_img=[]
        save_view_img=[]
        save_boxes=[]
        for count in range(start_frame, end_frame):
            im = im_array[count]
            im_copy = im.copy()
            self.show_images[count] = im_copy
            save_count.append(count)
            save_img.append(im_copy)
            if not self.init_once:
                for bbox_ in boxes:
                    ok = tracker.add(cv2.TrackerCSRT_create(), im, bbox_)
                self.init_once = True
            ok, bboxes = tracker.update(im)
            save_boxes.append(bboxes)
            for bbox in bboxes:
                if ok:
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(im, p1, p2, (255, 0, 0), 2, 1)
                else:
                    print(str(count) + ' frame error!')
                    break
                cv2.imshow("Tracking", im)
                time.sleep(0.1)
                # Exit if ESC pressed
                cv2.waitKey(1) & 0xff
            save_view_img.append(im)
        cv2.destroyAllWindows()
        self.init_once = False
        self.boxes = []
        self.save_flag = Tk()
        self.save_flag.geometry('200x100')
        Label(self.save_flag, text='save?').pack()
        Button(self.save_flag, text="Yes", command=lambda: self.save_data(save_count, save_img, save_view_img, save_boxes)).pack(side=LEFT, padx=35)
        Button(self.save_flag, text="No", command=self.save_flag.destroy).pack(side=RIGHT, padx=35)
        self.save_flag.mainloop()
    def load_imgarray(self, photo):
        self.c.xview_moveto(0)
        self.c.yview_moveto(0)
        self.c.create_image(0, 0, image=photo, anchor='nw', tags='img')
        self.c.config(scrollregion=self.c.bbox('all'), width=photo.width(), height=photo.height())
    def _on_mousewheel(self, event):
        if event.delta < 0:
            if self.wheel_num == self.start_frame:
                self.button_back = Button(self, text="Back", command=self.back, state=DISABLED)
            else:
                self.wheel_num -= 1
                self.boxes = []
                self.back(self.wheel_num)
        elif event.delta > 0:
            if self.wheel_num == self.end_frame-1:
                self.button_forward = Button(self, text="Forward", command=self.forward, state=DISABLED)
            else:
                self.wheel_num += 1
                self.boxes = []
                self.forward(self.wheel_num)

    def forward(self, img_no):
        self.wheel_num = img_no
        self.title(str(self.wheel_num) + '/' + str(len(self.List_images)-1))
        self.load_imgarray(self.List_images[self.wheel_num])

        # This is for clearing the screen so that
        # our next image can pop up
        self.c.bind_all("<MouseWheel>", self._on_mousewheel)

        # as the list starts from 0 so we are
        # subtracting one
        self.button_forward = Button(self.btnFrame, text="forward",
                            command=lambda: self.forward(img_no + 1))

        # img_no+1 as we want the next image to pop up
        if img_no == self.end_frame-1:
            self.button_forward = Button(self.btnFrame, text="Forward", command=self.forward,
                                    state=DISABLED)

        # img_no-1 as we want previous image when we click
        # back button
        self.button_back = Button(self.btnFrame, text="Back",
                             command=lambda: self.back(img_no - 1))

        btnfirst = Button(self.entryFrame, text="First", command=self.first_one)
        btnlast = Button(self.entryFrame, text="Last", command=self.last_one)
        btnfirst.grid(row=2, column=1, sticky='w')
        btnlast.grid(row=2, column=2, sticky='e')

        # Placing the button in new grid
        text = Label(self.entryFrame, text='select frame num: ')
        text.grid(row=0, column=1, sticky='en')
        start_end_frame = Entry(self.entryFrame)
        start_end_frame.insert(0, "e.g. -> 0~"+str(len(self.List_images)-1)+', number')
        start_end_frame.bind("<FocusIn>", lambda args: start_end_frame.delete('0', 'end'))
        start_end_frame.grid(row=0, column=2, sticky='en')
        start_end_frame.bind("<Return>", self.on_change)
        self.btntraker = Button(self.entryFrame, text="Traker",
                                command=lambda: self.start_tacker(self.show_images, self.wheel_num, self.end_frame, self.boxes))
        self.btntraker.grid(row=1, column=1, sticky='ew', columnspan=2)
        self.button_back.grid(row=0, column=0)
        self.button_exit.grid(row=0, column=1, padx=self.List_images[self.wheel_num].width()-300)
        self.button_forward.grid(row=0, column=2)
    def back(self, img_no):
        self.wheel_num = img_no
        self.title(str(self.wheel_num) + '/' + str(len(self.List_images)-1))
        self.load_imgarray(self.List_images[self.wheel_num])
        # This is for clearing the screen so that
        # our next image can pop up
        self.c.bind_all("<MouseWheel>", self._on_mousewheel)

        # for clearing the image for new image to pop up
        self.button_forward = Button(self.btnFrame, text="forward",
                                command=lambda: self.forward(img_no + 1))
        self.button_back = Button(self.btnFrame, text="Back",
                             command=lambda: self.back(img_no - 1))

        # whenever the first image will be there we will
        # have the back button disabled
        if img_no == self.start_frame:
            self.button_back = Button(self.btnFrame, text="Back", command=self.back, state=DISABLED)

        btnfirst = Button(self.entryFrame, text="First", command=self.first_one)
        btnlast = Button(self.entryFrame, text="Last", command=self.last_one)
        btnfirst.grid(row=2, column=1, sticky='w')
        btnlast.grid(row=2, column=2, sticky='e')

        text = Label(self.entryFrame, text='select frame num: ')
        text.grid(row=0, column=1, sticky='en')
        start_end_frame = Entry(self.entryFrame)
        start_end_frame.insert(0, "e.g. -> 0~"+str(len(self.List_images)-1)+', number')
        start_end_frame.bind("<FocusIn>", lambda args: start_end_frame.delete('0', 'end'))
        start_end_frame.grid(row=0, column=2, sticky='en')
        start_end_frame.bind("<Return>", self.on_change)
        self.btntraker = Button(self.entryFrame, text="Traker",
                                command=lambda: self.start_tacker(self.show_images, self.wheel_num, self.end_frame, self.boxes))
        self.btntraker.grid(row=1, column=1, sticky='ew', columnspan=2)
        self.button_back.grid(row=0, column=0)
        self.button_exit.grid(row=0, column=1, padx=self.List_images[self.wheel_num].width()-300)
        self.button_forward.grid(row=0, column=2)
    def on_mouse_down(self, event):
        self.anchor = (event.widget.canvasx(event.x),
                       event.widget.canvasy(event.y))
        self.item = None

    def on_mouse_drag(self, event):
        bbox = self.anchor + (event.widget.canvasx(event.x),
                              event.widget.canvasy(event.y))
        if self.item is None:
            self.item = event.widget.create_rectangle(bbox, outline="yellow")
        else:
            event.widget.coords(self.item, *bbox)

    def on_mouse_up(self, event):
        if self.item:
            self.on_mouse_drag(event)
            self.box = tuple((int(round(v)) for v in event.widget.coords(self.item)))
        self.boxes.append((self.box[0], self.box[1], self.box[2]-self.box[0], self.box[3]-self.box[1]))
        print(self.boxes)
    def on_right_click(self, event):
        found = event.widget.find_all()
        for iid in found:
            if event.widget.type(iid) == 'rectangle':
                event.widget.delete(iid)
                self.boxes = []
    def on_change(self, e):
        if e.widget.get() == 'raw':
            self.start_frame = 0
            self.end_frame = len(self.List_images)
        elif '~' in e.widget.get():
            start_frame, end_frame = e.widget.get().split('~')
            if start_frame.isdigit() and end_frame.isdigit():
                if int(start_frame) >= 0 and int(end_frame) < len(self.List_images):
                    self.start_frame = int(start_frame)
                    self.end_frame = int(end_frame) + 1
                    if self.wheel_num - int(end_frame) >= 0:
                        self.wheel_num = int(end_frame)
                    elif self.wheel_num - int(start_frame) < 0:
                        self.wheel_num = int(start_frame)
                else:
                    raise ValueError('frame number must between 0~'+str(len(self.List_images)-1))
            else:
                raise ValueError("must be integers on both sides of ~")
        elif e.widget.get().isdigit():
            if int(e.widget.get()) >= 0 and int(e.widget.get()) < len(self.List_images):
                self.start_frame = int(e.widget.get())
                self.end_frame = int(e.widget.get()) + 1
                self.wheel_num = int(e.widget.get())
            else:
                raise ValueError('frame number must between 0~'+str(len(self.List_images)-1))
        else:
            raise ValueError("must be integers")
        self.Open()
    def first_one(self):
        self.wheel_num = self.start_frame
        self.Open()
    def last_one(self):
        self.wheel_num = self.end_frame - 1
        self.Open()
    def Open(self):
        self.title(str(self.wheel_num) + '/' + str(len(self.List_images) - 1))
        self.load_imgarray(self.List_images[self.wheel_num])
        self.c.bind_all("<MouseWheel>", self._on_mousewheel)

        self.entryFrame = Frame(self, width=self.List_images[self.wheel_num].width(), height=200)
        self.entryFrame.grid(row=0, column=1)
        self.btnFrame = Frame(self, width=self.List_images[self.wheel_num].width(), height=200)
        self.btnFrame.grid(row=1, column=0)

        # We will have three button back ,forward and exit
        if self.wheel_num == self.start_frame:
            self.button_back = Button(self.btnFrame, text="Back", command=self.back,
                                 state=DISABLED)
        else:
            self.button_back = Button(self.btnFrame, text="Back",
                             command=lambda: self.back(self.wheel_num))

        # root.quit for closing the app
        self.button_exit = Button(self.btnFrame, text="Exit",
                             command=self.destroy)
        if self.wheel_num == self.end_frame:
            self.button_forward = Button(self.btnFrame, text="Forward", command=self.forward,
                                         state=DISABLED)
        else:
            self.button_forward = Button(self.btnFrame, text="Forward",
                                    command=lambda: self.forward(self.wheel_num))

        btnfirst = Button(self.entryFrame, text="First", command=self.first_one)
        btnlast = Button(self.entryFrame, text="Last", command=self.last_one)

        # grid function is for placing the buttons in the frame
        text = Label(self.entryFrame, text='select frame num: ')
        text.grid(row=0, column=1, sticky='en')

        start_end_frame = Entry(self.entryFrame)
        start_end_frame.insert(0,"e.g. -> 0~"+str(len(self.List_images)-1)+', number')
        start_end_frame.bind("<FocusIn>", lambda args: start_end_frame.delete('0', 'end'))
        start_end_frame.grid(row=0, column=2, sticky='en')
        start_end_frame.bind("<Return>", self.on_change)
        btnfirst.grid(row=2, column=1, sticky='w')
        btnlast.grid(row=2, column=2, sticky='e')

        self.btntraker = Button(self.entryFrame, text="Traker",
                                command=lambda: self.start_tacker(self.show_images, self.wheel_num, self.end_frame, self.boxes))

        self.btntraker.grid(row=1, column=1, sticky='ew', columnspan=2)
        self.button_back.grid(row=0, column=0)
        self.button_exit.grid(row=0, column=1, padx=self.List_images[self.wheel_num].width()-300)
        self.button_forward.grid(row=0, column=2)
        self.mainloop()